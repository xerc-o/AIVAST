import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


def parse_nmap_xml(xml_output: str) -> Dict:
    """
    Parse nmap XML output menjadi struktur data yang lebih terstruktur.
    
    Returns:
        Dict dengan struktur:
        {
            "hosts": [...],
            "ports": [...],
            "services": [...]
        }
    """
    try:
        root = ET.fromstring(xml_output)
        
        hosts = []
        ports = []
        services = []
        
        for host in root.findall('host'):
            host_info = {
                "status": host.find('status').get('state') if host.find('status') is not None else "unknown",
                "addresses": []
            }
            
            # Get addresses
            for address in host.findall('address'):
                host_info["addresses"].append({
                    "addr": address.get('addr'),
                    "addrtype": address.get('addrtype')
                })
            
            # Get ports
            ports_elem = host.find('ports')
            if ports_elem is not None:
                for port in ports_elem.findall('port'):
                    port_info = {
                        "port": port.get('portid'),
                        "protocol": port.get('protocol'),
                        "state": port.find('state').get('state') if port.find('state') is not None else "unknown",
                        "service": {}
                    }
                    
                    # Get service info
                    service_elem = port.find('service')
                    if service_elem is not None:
                        port_info["service"] = {
                            "name": service_elem.get('name', ''),
                            "product": service_elem.get('product', ''),
                            "version": service_elem.get('version', ''),
                            "extrainfo": service_elem.get('extrainfo', '')
                        }
                        services.append(port_info["service"])
                    
                    ports.append(port_info)
                    host_info["ports"] = ports
        
        hosts.append(host_info)
        
        return {
            "hosts": hosts,
            "ports": ports,
            "services": services,
            "parsed": True
        }
    except ET.ParseError as e:
        return {"parsed": False, "error": f"XML parse error: {str(e)}"}
    except Exception as e:
        return {"parsed": False, "error": f"Parse error: {str(e)}"}


def parse_nikto_xml(xml_output: str) -> Dict:
    """
    Parse nikto XML output menjadi struktur data yang lebih terstruktur.
    
    Returns:
        Dict dengan struktur:
        {
            "target": {...},
            "items": [...],
            "statistics": {...}
        }
    """
    try:
        root = ET.fromstring(xml_output)
        
        result = {
            "target": {},
            "items": [],
            "statistics": {},
            "parsed": True
        }
        
        # Parse target info
        scan_details = root.find('scandetails')
        if scan_details is not None:
            result["target"] = {
                "targetip": scan_details.get('targetip', ''),
                "targethostname": scan_details.get('targethostname', ''),
                "targetport": scan_details.get('targetport', ''),
                "targetbanner": scan_details.get('targetbanner', '')
            }
        
        # Parse items (vulnerabilities/issues)
        for item in root.findall('.//item'):
            item_info = {
                "id": item.get('id', ''),
                "osvdbid": item.get('osvdbid', ''),
                "osvdblink": item.get('osvdblink', ''),
                "description": item.find('description').text if item.find('description') is not None else '',
                "uri": item.find('uri').text if item.find('uri') is not None else '',
                "namelink": item.find('namelink').text if item.find('namelink') is not None else '',
                "iplink": item.find('iplink').text if item.find('iplink') is not None else ''
            }
            result["items"].append(item_info)
        
        # Parse statistics
        stats = root.find('statistics')
        if stats is not None:
            result["statistics"] = {
                "elapsed": stats.get('elapsed', ''),
                "itemsfound": stats.get('itemsfound', ''),
                "itemstested": stats.get('itemstested', '')
            }
        
        return result
    except ET.ParseError as e:
        return {"parsed": False, "error": f"XML parse error: {str(e)}"}
    except Exception as e:
        return {"parsed": False, "error": f"Parse error: {str(e)}"}


def _get_xml_content(stdout: str, stderr: str) -> Optional[str]:
    """Extracts XML content from stdout or stderr."""
    if "<?xml" in stdout:
        return stdout
    if "<?xml" in stderr:
        return stderr
    return None


def extract_structured_data(tool: str, stdout: str, stderr: str = "") -> Dict:
    """
    Extract structured data dari output tool.
    
    Args:
        tool: Tool name ("nmap" atau "nikto")
        stdout: Standard output dari tool
        stderr: Standard error dari tool
    
    Returns:
        Dict dengan structured data atau empty dict jika parsing gagal
    """
    xml_content = _get_xml_content(stdout, stderr)
    if not xml_content:
        return {"parsed": False, "format": "text"}

    if tool == "nmap":
        return parse_nmap_xml(xml_content)
    
    elif tool == "nikto":
        return parse_nikto_xml(xml_content)
    
    return {"parsed": False, "error": "Unknown tool"}