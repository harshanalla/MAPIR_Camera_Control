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
        },
        "Survey3": {
            "pre_process": {
                "filters": ["RGB", "OCN", "RGN", "NGB", "RE", "NIR"],
                "lenses": ["3.37mm (Survey3W)", "8.25mm (Survey3N)"],
                "enable_filter_select": True,
                "enable_lens_select": True,
                "enable_dark_box": True
            }
        },
        "Survey2": {
            "pre_process": {
                "filters": ["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"],
                "lenses": ["3.97mm"],
                "enable_filter_select": True,
                "enable_lens_select": False,
                "enable_dark_box": True
            }
        },
        "Survey1": {
            "pre_process": {
                "filters": ["Blue + NIR (NDVI)"],
                "lenses": ["3.97mm"],
                "enable_filter_select": False,
                "enable_lens_select": False,
                "enable_dark_box": False
            }
        },
        "DJI Phantom 4": {
            "pre_process": {
                "filters": ["Red + NIR (NDVI)"],
                "lenses": ["3.97mm"],
                "enable_filter_select": False,
                "enable_lens_select": False,
                "enable_dark_box": False
            }
        },
        "DJI Phantom 4 Pro": {
            "pre_process": {
                "filters": ["RGN"],
                "lenses": ["3.97mm"],
                "enable_filter_select": False,
                "enable_lens_select": False,
                "enable_dark_box": False
            }
        },
        "DJI Phantom 3a": {
            "pre_process": {
                "filters": ["Red + NIR (NDVI)"],
                "lenses": ["3.97mm"],
                "enable_filter_select": False,
                "enable_lens_select": False,
                "enable_dark_box": False
            }
        },
        "DJI Phantom 3p": {
            "pre_process": {
                "filters": ["Red + NIR (NDVI)"],
                "lenses": ["3.97mm"],
                "enable_filter_select": False,
                "enable_lens_select": False,
                "enable_dark_box": False
            }
        },
        "DJI X3": {
            "pre_process": {
                "filters": ["Red + NIR (NDVI)"],
                "lenses": ["3.97mm"],
                "enable_filter_select": False,
                "enable_lens_select": False,
                "enable_dark_box": False
            }
        },
    }
