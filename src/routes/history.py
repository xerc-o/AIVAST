from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, ScanHistory
from sqlalchemy import desc

history_bp = Blueprint("history", __name__)

@history_bp.route("/scans", methods=["GET"])
@login_required
def list_scans():
    """List semua scan history dengan pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    tool_filter = request.args.get("tool", None)
    risk_filter = request.args.get("risk", None)
    
    query = ScanHistory.query.filter_by(user_id=current_user.id)
    
    # Filters
    if tool_filter:
        query = query.filter(ScanHistory.tool == tool_filter)
    if risk_filter:
        query = query.filter(ScanHistory.risk_level == risk_filter)
    
    # Pagination
    pagination = query.order_by(desc(ScanHistory.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    scans = [scan.to_dict() for scan in pagination.items]
    
    return jsonify({
        "scans": scans,
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages
    })

@history_bp.route("/scans/<int:scan_id>", methods=["GET"])
@login_required
def get_scan(scan_id):
    """Get detail scan tertentu."""
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    return jsonify(scan.to_dict())

@history_bp.route("/scans/<int:scan_id>", methods=["DELETE"])
@login_required
def delete_scan(scan_id):
    """Delete scan tertentu."""
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    db.session.delete(scan)
    db.session.commit()
    return jsonify({"message": "Scan deleted successfully"})