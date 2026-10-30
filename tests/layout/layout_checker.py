from dataclasses import dataclass


@dataclass
class LayoutChecker:
    def check_coordinates(self):
        pass

    def check_distance(self):
        pass

    def check_cz_neighbours(self):
        pass

    def check_too_close_pais(self):
        pass

    def check_convert_to_register(self):
        pass
