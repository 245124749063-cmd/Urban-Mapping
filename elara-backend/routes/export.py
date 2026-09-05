from flask import Blueprint, request, send_file, jsonify, current_app
import geopandas as gpd
from shapely.geometry import shape
import pandas as pd
import json
import os
import shutil
import zipfile

export_bp = Blueprint('export', __name__)


@export_bp.route('/api/v1/export', methods=['POST'])
def export_gis():

    try:
        data = request.json or {}

        export_format = data.get('format', 'geojson').lower()
        geojson_data = data.get('geojson', {})

        if not geojson_data:
            return jsonify({
                "error": "No GeoJSON payload provided"
            }), 400

        export_dir = current_app.config['EXPORT_FOLDER']
        os.makedirs(export_dir, exist_ok=True)

        filename_base = "ELARA_Cadastral_Export"

        # ---------------------------------
        # GEOJSON
        # ---------------------------------
        if export_format == 'geojson':

            out_path = os.path.join(
                export_dir,
                f"{filename_base}.geojson"
            )

            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, indent=2)

            return send_file(
                out_path,
                as_attachment=True,
                download_name=f"{filename_base}.geojson"
            )

        # ---------------------------------
        # FEATURES
        # ---------------------------------
        features = geojson_data.get('features', [])

        if not features:
            return jsonify({
                "error": "GeoJSON contains no features"
            }), 400

        geoms = []
        properties = []

        for feature in features:

            geometry = feature.get('geometry')

            if not geometry:
                continue

            try:
                geoms.append(shape(geometry))
                properties.append(
                    feature.get('properties', {})
                )
            except Exception:
                continue

        if not geoms:
            return jsonify({
                "error": "No valid geometries found"
            }), 400

        # Current demo uses pixel coordinates.
        # Do NOT claim EPSG:4326 for this data.
        gdf = gpd.GeoDataFrame(
            properties,
            geometry=geoms,
            crs=None
        )

        # ---------------------------------
        # SHAPEFILE
        # ---------------------------------
        if export_format in ['shapefile', 'shp']:

            shp_folder = os.path.join(
                export_dir,
                "ELARA_Cadastral_Shapefile"
            )

            # Remove old folder if it exists
            if os.path.exists(shp_folder):
                shutil.rmtree(shp_folder)

            os.makedirs(shp_folder, exist_ok=True)

            shp_path = os.path.join(
                shp_folder,
                f"{filename_base}.shp"
            )

            # Write actual Shapefile components
            gdf.to_file(
                shp_path,
                driver='ESRI Shapefile'
            )

            # Create ZIP containing .shp/.shx/.dbf/.prj/etc.
            zip_path = os.path.join(
                export_dir,
                f"{filename_base}.zip"
            )

            if os.path.exists(zip_path):
                os.remove(zip_path)

            with zipfile.ZipFile(
                zip_path,
                'w',
                zipfile.ZIP_DEFLATED
            ) as zipf:

                for filename in os.listdir(shp_folder):

                    file_path = os.path.join(
                        shp_folder,
                        filename
                    )

                    zipf.write(
                        file_path,
                        arcname=filename
                    )

            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"{filename_base}.zip"
            )

        # ---------------------------------
        # CSV
        # ---------------------------------
        elif export_format == 'csv':

            out_path = os.path.join(
                export_dir,
                f"{filename_base}.csv"
            )

            df = pd.DataFrame(properties)

            df.to_csv(
                out_path,
                index=False
            )

            return send_file(
                out_path,
                as_attachment=True,
                download_name=f"{filename_base}.csv"
            )

        # ---------------------------------
        # UNSUPPORTED
        # ---------------------------------
        return jsonify({
            "error": "Unsupported export format"
        }), 400

    except Exception as e:

        print("ELARA EXPORT ERROR:", str(e))

        return jsonify({
            "error": "Internal Server Error in ELARA Export Pipeline",
            "details": str(e)
        }), 500