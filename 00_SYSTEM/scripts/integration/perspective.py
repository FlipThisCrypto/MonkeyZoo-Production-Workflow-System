"""Single-point ground-plane height-line scaling.

Classic matte-painting technique: pick the horizon line (y_horizon) and one
calibration point where a known apparent height (calib_height_px) sits on
the ground plane at a known foot y (calib_y). Apparent height of anything
else standing on the same ground plane scales linearly with vertical
distance from the horizon:

    scale(y_foot) = calib_height_px * (y_foot - y_horizon) / (calib_y - y_horizon)

This holds for any object resting on a flat ground plane viewed with a
standard (non-fisheye) lens, regardless of the object's real-world size --
it only requires that horizon_y and the calibration point are correct for
the *scene*, not the character.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GroundPlane:
    horizon_y: float
    calib_y: float
    calib_height_px: float

    def __post_init__(self) -> None:
        # Guard degenerate calibrations that would make height_at /
        # foot_y_for_height divide by zero -- surface a clear error at
        # construction instead of a raw ZeroDivisionError deep in the compositor.
        if self.calib_y == self.horizon_y:
            raise ValueError(
                f"degenerate ground plane: calib_y ({self.calib_y}) coincides with "
                f"horizon_y ({self.horizon_y}); the calibration foot cannot sit on the horizon")
        if self.calib_height_px <= 0:
            raise ValueError(f"calib_height_px must be positive, got {self.calib_height_px}")

    def height_at(self, y_foot: float) -> float:
        if y_foot <= self.horizon_y:
            raise ValueError(f"y_foot={y_foot} is above the horizon ({self.horizon_y}); "
                              "cannot stand there on this ground plane")
        return self.calib_height_px * (y_foot - self.horizon_y) / (self.calib_y - self.horizon_y)

    def foot_y_for_height(self, height_px: float) -> float:
        return self.horizon_y + height_px * (self.calib_y - self.horizon_y) / self.calib_height_px
