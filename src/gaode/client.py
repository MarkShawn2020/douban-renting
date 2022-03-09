from gaode.base import GaodeBase


class GaodeClient(GaodeBase):
    """
    这是对 `GaodeBase` 的一个封装，每次调用api时不用再输入 `city` 和 `target_address` 等信息
    """

    def __init__(self, city, target_address):
        super().__init__()
        self.city = city
        self.target_address = target_address
        self.target_coordinates = self.get_coords_from_addr(self.target_address)

    def get_coords_from_addr(self, addr: str):
        return super()._get_coords_from_addr(addr, self.city)

    def calc_transit_duration_from_coords(self, from_coords):
        return super()._calc_transit_duration_between_coords(from_coords, self.target_coordinates, self.city)

