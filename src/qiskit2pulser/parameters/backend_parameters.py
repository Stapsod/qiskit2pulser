class BackendParameters:
    type: str
    positions: list[tuple[float, float]] | None = None

    def add_positions(self, positions: list[tuple[float, float]]) -> None:
        self.positions = positions
