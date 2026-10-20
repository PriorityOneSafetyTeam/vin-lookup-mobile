import flet as ft
import requests

def lookup_vehicle_by_vin(vin: str):
    """Looks up vehicle data using the official NHTSA vPIC API endpoint."""
    clean_vin = "".join(vin.split()).upper()
    if len(clean_vin) != 17:
        return {"error": f"Invalid VIN Length: {len(clean_vin)} characters. Must be exactly 17."}

    url = f"https://dot.gov{clean_vin}?format=json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Mobile API Dashboard)",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_data = response.json()

        clean_results = {}
        for item in raw_data.get("Results", []):
            variable_name = item.get("Variable")
            variable_value = item.get("Value")
            if variable_value and str(variable_value).strip():
                val_str = str(variable_value).strip()
                if val_str.lower() not in ["not applicable", "none", "null"]:
                    clean_results[variable_name] = val_str
        return clean_results
    except requests.exceptions.RequestException as e:
        return {"error": f"Could not reach database.\n\nError: {e}"}

def main(page: ft.Page):
    page.title = "POST Vehicle Inquiry Service"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 20
    
    # Core Mobile UI Themes
    accent_blue = "#1e40af"
    text_muted = "#475569"

    # UI Widgets
    title = ft.Text("POST Vehicle Inquiry", style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight=ft.FontWeight.BOLD)
    vin_input = ft.TextField(label="Enter 17-Digit VIN Number", max_length=17, capitalize=ft.TextCapitalization.CHARACTERS, hint_text="17 alphanumeric characters")
    results_container = ft.Column(spacing=10, expand=True)

    def show_alert(message):
        page.overlay.append(ft.AlertDialog(title=ft.Text("Alert"), content=ft.Text(message), open=True))
        page.update()

    def perform_search(e):
        results_container.controls.clear()
        vin = vin_input.value.strip()
        
        if not vin:
            show_alert("Please type a valid VIN code first.")
            return

        page.overlay.append(ft.ProgressRing())
        page.update()

        data = lookup_vehicle_by_vin(vin)
        page.overlay.clear()

        if "error" in data:
            show_alert(data["error"])
            return
        
        if not data:
            show_alert("No vehicle configuration items found.")
            return

        # Display Main Specific Core Elements
        results_container.controls.append(ft.Text("Core Identity Overview", size=18, weight=ft.FontWeight.BOLD, color=accent_blue))
        primary_metrics = ["Model Year", "Make", "Model", "Trim", "Body Class"]
        
        for metric in primary_metrics:
            if metric in data:
                results_container.controls.append(ft.Row([
                    ft.Text(f"{metric}: ", weight=ft.FontWeight.BOLD, color=text_muted, width=140),
                    ft.Text(data[metric], color="black", expand=True)
                ]))
                del data[metric]

        results_container.controls.append(ft.Divider())
        results_container.controls.append(ft.Text("Additional Engine Specs", size=16, weight=ft.FontWeight.BOLD))

        for key in sorted(data.keys()):
            if key in ["Error Code", "Error Text"]:
                continue
            results_container.controls.append(ft.Row([
                ft.Text(f"{key}: ", weight=ft.FontWeight.BOLD, color=text_muted, width=140),
                ft.Text(data[key], color="black", expand=True)
            ]))
        
        page.update()

    def clear_fields(e):
        vin_input.value = ""
        results_container.controls.clear()
        results_container.controls.append(ft.Text("Please enter a vehicle VIN above to query specification sheets.", italic=True, color=text_muted))
        page.update()

    # Initial Setup Text Description State
    results_container.controls.append(ft.Text("Please enter a vehicle VIN above to query specification sheets.", italic=True, color=text_muted))

    # Control Action Buttons Row Layout Layout
    buttons_row = ft.Row([
        ft.ElevatedButton("Search Database", on_click=perform_search, bgcolor=accent_blue, color="white", expand=True),
        ft.OutlinedButton("Clear", on_click=clear_fields)
    ])

    page.add(title, vin_input, buttons_row, ft.Container(content=results_container, padding=10))

# Boot target configured seamlessly for running inside cloud web ports
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)