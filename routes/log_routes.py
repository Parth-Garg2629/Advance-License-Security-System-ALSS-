from flask import Blueprint, jsonify, request, Response
from auth.decorators import token_required, roles_required
from services.log_service import get_recent_logs, export_logs_csv

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/api/logs", methods=["GET"])
@token_required
@roles_required("ADMIN")
def list_logs():
    limit = int(request.args.get("limit", 100))
    return jsonify({"logs": get_recent_logs(limit)})

@logs_bp.route("/api/logs/export", methods=["GET"])
@token_required
@roles_required("ADMIN")
def export_logs():
    limit = int(request.args.get("limit", 1000))
    csv_data = export_logs_csv(limit)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )
