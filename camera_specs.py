class CameraSpecs(object):

    specs = {
        "Kernel 3.2": {
            "pre_process": {
                "filters": [
                    "405", "450", "490", "518", "550", "590", "615", "632", "650",
                    "685", "725", "780", "808", "850", "880", "940", "945", "NO FILTER"
                ],
                "lenses": ["9.6mm", "3.5mm"],
                "enable_filter_select": True,
                "enable_lens_select": True,
                "enable_dark_box": True
            }
        },
        "Kernel 14.4": {
            "pre_process": {
                "filters": ["550/660/850", "475/550/850", "644 (RGB)", "850", "OCN"],
                "lenses": ["3.37mm", "8.25mm"],
                "enable_filter_select": True,
                "enable_lens_select": True,
                "enable_dark_box": True
            }
        }
    }
