# app.py — Shiny for Python: three-column form + Leaflet map in Core section
# - Map displays belgium_map_simplified.shp
# - Clicking a region writes its `nouveau_PO` into the postal_code field (numeric input)

from shiny import App, ui, render, reactive
import geopandas as gpd

# ---- Load shapefile and prepare GeoJSON ----
# Expecting: ./shapefiles/belgium_map_simplified.shp with a 'nouveau_PO' property
gdf = gpd.read_file("./shapefiles/belgium_map_simplified.shp")
geojson_data = gdf.to_json()

app_ui = ui.page_fluid(
    ui.h3("Describe your property"),

    # Leaflet CSS/JS (once per app)
    ui.tags.link(
        rel="stylesheet",
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    ),
    ui.tags.script(src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"),

    # --- Three columns layout (Core / Details / Extras) ---
    ui.layout_columns(

        # Column 1 — Core fields + MAP + postal_code under the map
        ui.card(
            ui.card_header("Describe your property:",
                            style="color: red; font-weight: bold;font-size: 1.3rem;"),

            # Postal code directly under the map; filled by map click
            ui.input_numeric("postal_code", "Postal code (select on the map):", value=9000, min=1000, max=9999, step=1),

            # Map container (fixed height; adjusts inside card width)
            ui.tags.div(
                id="map",
                style=(
                    "height: 320px; width: 100%; "
                    "border: 1px solid #ccc; margin-bottom: 10px;"
                ),
            ),

            # Core numeric fields
            ui.input_numeric("rooms", "Rooms:", value=None, min=1, max=15, step=1),           # required
            ui.input_numeric("area", "Area (m2):", value=None, min=10, max=600, step=1),      # required

            ui.input_select(
                "property_type",
                "Property type:",
                choices={"": "", "house": "House", "apartment": "Apartment"},
                selected=""
            ),
            ui.input_select(
                "property_subtype",
                "Property subtype:",
                choices={
                    "": "",
                    "studio": "Studio",
                    "duplex": "Duplex",
                    "residence": "Residence",
                    "villa": "Villa",
                    "other": "Other",
                },
                selected=""
            ),
        ),

        # Column 2 — additional details and binary switches
        ui.card(
            ui.card_header("Details",style="color: blue;"),
            ui.input_numeric("number_floors", "Number of floors:", value=None, min=1, max=10, step=1),  # required

            ui.input_numeric("bathrooms", "Bathrooms:", value=1, min=1, max=5, step=1),  # optional (default 1)
            ui.input_numeric("toilets", "Toilets:", value=1, min=1, max=5, step=1),      # optional (default 1)

            ui.input_select(
                "equipped_kitchen",
                "Equipped kitchen:",
                choices={
                    "Not equipped": "Not equipped",
                    "Partially equipped": "Partially equipped",
                    "Fully equipped": "Fully equipped",
                },
                selected="Fully equipped"
            ),

            ui.input_switch("has_swimming_pool", "Swimming pool", value=False),
            ui.input_switch("has_terrace", "Terrace", value=False),
            ui.input_switch("has_garden", "Garden", value=False),
            ui.input_switch("has_garage", "Garage", value=False),
            ui.input_switch("elevator", "Elevator", value=False),
            ui.input_switch("is_furnished", "Furnished", value=False),
        ),

        # Column 3 — optional extras
        ui.card(
            ui.card_header("Extras",style="color: blue;"),
            ui.input_numeric("facades_number", "Facades number:", value=None, min=1, max=4, step=1),
            ui.input_numeric("build_year", "Build year:", value=None, min=1800, max=2024, step=1),
            ui.input_numeric("cadastral_income", "Cadastral income:", value=None, min=0, step=1),
            ui.input_numeric(
                "primary_energy_consumption",
                "Primary energy consumption (kWh/m2):",
                value=None, min=0, max=1200, step=1
            ),
        ),
    ),

    ui.br(),
    ui.input_action_button("submit", "Submit"),
    ui.br(),
    ui.output_text_verbatim("result"),

    # ---- Inline JS: render Leaflet map and wire clicks to postal_code input ----
    ui.tags.script(
        f"""
        (function() {{
          const geojson = {geojson_data};

          function initMap() {{
            if (!window.L) return; // Leaflet not loaded yet

            const container = document.getElementById("map");
            if (!container) return;

            // Prevent re-init if navigating/hot-reloading
            if (container._leaflet_id) return;

            const map = L.map('map').setView([50.85, 4.35], 8);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
              maxZoom: 19
            }}).addTo(map);

            function style(feature) {{
              return {{
                weight: 0.5,
                color: "#666",
                fillColor: "#cccccc",
                fillOpacity: 0
              }};
            }}

            function highlightFeature(e) {{
              const layer = e.target;
              layer.setStyle({{
                weight: 2,
                color: '#cc0066',
                fillOpacity: 0.3
              }});
              if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {{
                layer.bringToFront();
              }}
            }}

            function resetHighlight(e) {{
              geoLayer.resetStyle(e.target);
            }}

            function onClickFeature(e, feature) {{
              const v = feature?.properties?.nouveau_PO ?? "";
              const text = v ? ("Postal code: " + v) : "No data";
              // e.target.bindPopup(text).openPopup(e.latlng);

              // Write value into numeric input and notify Shiny
              const field = document.getElementById("postal_code");
              if (field) {{
                field.value = v; // numeric <input> accepts numeric strings
                field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                field.dispatchEvent(new Event('change', {{ bubbles: true }}));
              }}
            }}

            const geoLayer = L.geoJSON(geojson, {{
              style: style,
              onEachFeature: function (feature, layer) {{
                layer.on({{
                  mouseover: highlightFeature,
                  mouseout: resetHighlight,
                  click: function(e) {{ onClickFeature(e, feature); }}
                }});
              }}
            }}).addTo(map);

            try {{
              map.fitBounds(geoLayer.getBounds());
            }} catch (e) {{
              // ignore if bounds unavailable
            }}
          }}

          // Initialize after DOM ready and when Shiny is idle (covers hot-reload)
          if (document.readyState === "loading") {{
            document.addEventListener("DOMContentLoaded", initMap);
          }} else {{
            initMap();
          }}
          document.addEventListener("shiny:idle", initMap);
        }})();
        """
    ),
)

def server(input, output, session):
    # Collect inputs and apply server-side defaults for some optional fields
    def collect_and_clean():
        data = {
            "rooms": input.rooms(),
            "area": input.area(),
            "property_type": input.property_type() or None,
            "property_subtype": input.property_subtype() or None,

            "number_floors": input.number_floors(),
            "bathrooms": input.bathrooms(),   # optional
            "toilets": input.toilets(),       # optional
            "equipped_kitchen": input.equipped_kitchen(),

            "has_swimming_pool": bool(input.has_swimming_pool()),
            "has_terrace": bool(input.has_terrace()),
            "has_garden": bool(input.has_garden()),
            "has_garage": bool(input.has_garage()),
            "elevator": bool(input.elevator()),
            "is_furnished": bool(input.is_furnished()),

            # Server-side defaults when missing
            "facades_number": input.facades_number() if input.facades_number() is not None else 3,
            "build_year": input.build_year() if input.build_year() is not None else 2011,

            # Leave None for server-side handling
            "cadastral_income": input.cadastral_income(),
            "primary_energy_consumption": input.primary_energy_consumption(),

            "postal_code": input.postal_code(),  # optional; default 9000 in UI; filled by map when clicked
        }
        return data

    # Validate required fields only
    def validate_required():
        errors = []
        if input.rooms() is None:
            errors.append("Rooms is required")
        if input.area() is None:
            errors.append("Area is required")
        if input.number_floors() is None:
            errors.append("Number of floors is required")
        return errors

    @reactive.Effect
    @reactive.event(input.submit)
    def _on_submit():
        ui.notification_remove()

        errors = validate_required()
        if errors:
            for e in errors:
                ui.notification_show(e, type="error", duration=None)
            return

        data = collect_and_clean()
        lines = [f"{k}: {v}" for k, v in data.items()]
        output_text = "Submitted data:\n" + "\n".join(lines)
        ui.notification_show("Form submitted.", type="message", duration=3)
        _set_result(output_text)

    @output
    @render.text
    def result():
        return "Fill the form and press Submit."

    # Internal helper to update the result output
    def _set_result(text: str):
        @output
        @render.text
        def result():
            return text


app = App(app_ui, server)
