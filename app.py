# app.py — Shiny for Python: three-column form + Leaflet map in Core section
# - Map displays belgium_map_simplified.shp
# - Clicking a region writes its `nouveau_PO` into the postal_code field (numeric input)

from shiny import App, ui, render, reactive



from model_price import calculate_price



####################################################################################

if(1):
    
    import json
    
    with open('./data/belgium_map.geojson') as f:
        geojson_data_raw = json.load(f)
        geojson_data = json.dumps(geojson_data_raw)

if(0):
    
    import geopandas as gpd
    
    gdf = gpd.read_file("./shapefiles/belgium_map_simplified.shp")
    geojson_data = gdf.to_json()


app_ui = ui.page_fluid(


    # --- TOP ROW: BUTTON + PRICE (ONE LINE) ---
    ui.tags.div(

        # Button on the left
        ui.input_action_button(
            "submit",
            "Evaluate property",
            style=(
                "border: 2px solid #28a745; "
                "color: #28a745; "
                "font-weight: bold; "
                "background-color: white; "
                "padding: 6px 14px; "
                "border-radius: 6px; "
                "cursor: pointer;"
            )
        ),

        # Right: label + price field
        ui.tags.div(

            # Label
            ui.tags.label(
                "Estimated price:",
                **{"for": "price"},
                style="color: #0074D9; font-weight: bold;"
            ),

            # PRICE INPUT (disabled, no inline style inside input)
            ui.tags.div(
                ui.input_text(
                    "price",
                    label=None,
                    value=""
                ),
                style=(
                    "font-weight: bold;"
                    "padding: 4px 6px;"
                    "width: 40%;"
                    "margin-bottom: 0;"              
                )
            ),

            style="display: flex; align-items: center; gap: 6px;",
        ),

        style=(
            "display: flex; "
            "align-items: center; "
            "justify-content: center; "
            "gap: 60px; "
            "width: 100%; "
            "margin-bottom: 10px;"
        ),
    ),
    
ui.tags.script("""
(function lock() {
  var el = document.querySelector('input#price');
  if (!el) { setTimeout(lock, 50); return; }

  el.readOnly = true;
  el.setAttribute('readonly', 'readonly');
  el.style.border = "2px solid #0074D9";
  el.style.fontWeight = "bold";
  
  el.style.transform = "translateY(8px)";
})();
"""),
    
    
    
# --- TRIPLE THIN DIVIDER ---
ui.tags.div(
    style=(
        "height: 10px;"
        "background-image:"
        "linear-gradient(#cc0099, #cc0099),"
        "linear-gradient(#cc0099, #cc0099),"
        "linear-gradient(#cc0099, #cc0099);"
        "background-repeat: no-repeat;"
        "background-size: 100% 1px, 100% 1px, 100% 1px;"
        "background-position: 0 0, 0 50%, 0 100%;"
        "margin: 12px 0;"
    )
),
    
    
   

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

            ui.input_switch("is_furnished", "Is furnished?", value=False),
            ui.input_switch("has_swimming_pool", "Swimming pool", value=False),
            ui.input_switch("has_terrace", "Terrace", value=False),
            ui.input_switch("has_garden", "Garden", value=False),
            ui.input_switch("has_garage", "Garage", value=False),
            ui.input_switch("elevator", "Elevator", value=False),
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

def collect_data(input):
    return {
        "postal_code": input.postal_code(),
        "rooms": input.rooms(),
        "area": input.area(),
        "number_floors": input.number_floors(),
        "bathrooms": input.bathrooms(),
        "toilets": input.toilets(),
        "equipped_kitchen": input.equipped_kitchen(),
        "property_type": input.property_type(),
        "property_subtype": input.property_subtype(),
        "has_swimming_pool": input.has_swimming_pool(),
        "has_terrace": input.has_terrace(),
        "has_garden": input.has_garden(),
        "has_garage": input.has_garage(),
        "elevator": input.elevator(),
        "is_furnished": input.is_furnished(),
        "facades_number": input.facades_number(),
        "build_year": input.build_year(),
        "cadastral_income": input.cadastral_income(),
        "primary_energy_consumption": input.primary_energy_consumption(),
    }

def server(input, output, session):

    @reactive.Effect
    @reactive.event(input.submit)
    def _on_submit():
        # Collect all form values into a dictionary
        data = collect_data(input)

        # Calculate the price using external logic from model_price.py
        price_value = calculate_price(data)

        # Format the price with euro sign and spacing
        formatted_price = f"€ {price_value:,.0f}".replace(",", " ")

        # Update the price field in UI
        ui.update_text("price", value=formatted_price)

        # Optional: debug output to console
        #print("Received form data:", data)
        #print("Calculated price:", formatted_price)



app = App(app_ui, server)
