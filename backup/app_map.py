from shiny import App, ui
import geopandas as gpd

# Load shapefile
gdf = gpd.read_file("./shapefiles/belgium_map_simplified.shp")

# Convert to GeoJSON
geojson_data = gdf.to_json()

app_ui = ui.page_fluid(

    ui.h2("Belgium map with nouveau_PO"),

    ui.input_text("postal_code", "Postal code:", value=""),

    ui.tags.div(id="map", style="height: 300px; width:800px; border: 1px solid #ccc; margin-top: 10px;"),

    # Leaflet CSS + JS
    ui.tags.link(
        rel="stylesheet",
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    ),
    ui.tags.script(src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"),

    # JavaScript logic
    ui.tags.script(
        f"""
        const geojson = {geojson_data};

        document.addEventListener("DOMContentLoaded", () => {{

            function style(feature) {{
                return {{
                    weight: 0.5,
                    color: "#666",
                    fillColor: "#cccccc",
                    fillOpacity: 0.4
                }};
            }}

            function highlightFeature(e) {{
                const layer = e.target;
                layer.setStyle({{
                    weight: 2,
                    color: '#000',
                    fillOpacity: 0.7
                }});
                layer.bringToFront();
            }}

            function resetHighlight(e) {{
                geoLayer.resetStyle(e.target);
            }}

            function onClickFeature(e, feature) {{
                const v = feature.properties?.nouveau_PO;
                const text = v ? ("nouveau_PO: " + v) : "No data";

                e.target.bindPopup(text).openPopup(e.latlng);

                // Insert nouveau_PO into input field
                const field = document.getElementById("postal_code");
                if (field) {{
                    field.value = v ?? "";
                }}
            }}

            const map = L.map('map').setView([50.85, 4.35], 8);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19
            }}).addTo(map);

            const geoLayer = L.geoJSON(geojson, {{
                style: style,
                onEachFeature: function(feature, layer) {{
                    layer.on({{
                        mouseover: highlightFeature,
                        mouseout: resetHighlight,
                        click: function(e) {{ onClickFeature(e, feature); }}
                    }});
                }}
            }}).addTo(map);

            map.fitBounds(geoLayer.getBounds());
        }});
        """
    )
)

app = App(app_ui, server=None)
