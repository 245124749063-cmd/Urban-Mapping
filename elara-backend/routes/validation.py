from flask import Blueprint, request, jsonify
from utils.geo_processing import check_topology_errors

validation_bp = Blueprint('validation', __name__)

@validation_bp.route('/api/v1/validate-topology', methods=['POST'])
def validate_topology():
    data = request.json or {}
    features = data.get('features', [])
    
    anomalies = check_topology_errors(features)
    
    return jsonify({
        "status": "validated",
        "total_anomalies": len(anomalies),
        "anomalies": anomalies
    }), 200