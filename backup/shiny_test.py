"""
shiny example
""" 

from shiny import App, ui, render

###########################################

app_ui = ui.page_fluid(
    ui.input_text("name", "Your name:"),
    ui.output_text("greeting"),
)

def server(input, output, session):
    @render.text
    def greeting():
        return f"Hello, {input.name()}!"

app = App(app_ui, server)

#############################################

print('\nTask completed!')

#############################################
