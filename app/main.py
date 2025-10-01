# Import required dependencies
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import itertools
import os

app = FastAPI(title="Vehicle Search")

# Load listings.json from same directory as main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LISTINGS_PATH = os.path.join(BASE_DIR, "listings.json")
if not os.path.exists(LISTINGS_PATH):
    raise RuntimeError(f"listings.json not found at {LISTINGS_PATH}. Place file there.")

with open(LISTINGS_PATH, "r", encoding="utf-8") as f:
    ALL_LISTINGS: List[Dict[str, Any]] = json.load(f)

# Build lookup by location
LISTINGS_BY_LOCATION: Dict[str, List[Dict[str, Any]]] = {}
for L in ALL_LISTINGS:
    LISTINGS_BY_LOCATION.setdefault(L["location_id"], []).append(L)


class VehicleRequestItem(BaseModel):
    length: int
    quantity: int


def expand_vehicles(req_items: List[Dict[str, int]]) -> List[int]:
    """Return list of vehicle lengths (feet), expanded by quantity."""
    vehicles = []
    for it in req_items:
        L = it["length"]
        q = it["quantity"]
        for _ in range(q):
            vehicles.append(L)
    return vehicles


def can_pack_into_rows(row_count: int, row_len_cells: int, vehicle_cells: List[int]) -> bool:
    """
    Try to pack the given list of vehicle lengths (in cells) into row_count rows,
    each with capacity row_len_cells. Use backtracking placing each vehicle into a row.
    """
    # sort descending to prune faster
    vehicle_cells_sorted = sorted(vehicle_cells, reverse=True)
    # quick fail: any vehicle longer than row length can't fit
    if any(v > row_len_cells for v in vehicle_cells_sorted):
        return False

    # row remaining capacities
    rows = [row_len_cells] * row_count

    # backtracking
    def place(idx: int) -> bool:
        if idx == len(vehicle_cells_sorted):
            return True
        v = vehicle_cells_sorted[idx]
        seen = set()
        for r in range(row_count):
            if rows[r] >= v and rows[r] not in seen:
                # place in row r
                rows[r] -= v
                if place(idx + 1):
                    return True
                rows[r] += v
                seen.add(rows[r])  # avoid equivalent states
        return False

    return place(0)


def listing_can_fit_assigned(listing: Dict[str, Any], assigned_vehicle_lengths: List[int]) -> bool:
    """
    Determine whether the assigned vehicles (lengths in feet) can be packed into this listing,
    choosing the best orientation for that listing (orientation must be same for all assigned vehicles).
    """
    if not assigned_vehicle_lengths:
        return True

    # convert listing dims to cells (10ft per cell)
    list_len_cells = listing["length"] // 10
    list_wid_cells = listing["width"] // 10

    # Convert vehicle lengths to cells
    veh_cells = [L // 10 for L in assigned_vehicle_lengths]

    # Orientation A: vehicle length aligned with listing.length
    rows_A = list_wid_cells
    row_len_A = list_len_cells
    okA = can_pack_into_rows(rows_A, row_len_A, veh_cells)

    # Orientation B: vehicle length aligned with listing.width (swap)
    rows_B = list_len_cells
    row_len_B = list_wid_cells
    okB = can_pack_into_rows(rows_B, row_len_B, veh_cells)

    return okA or okB


@app.post("/", response_model=List[Dict[str, Any]])
def search_vehicle(request: List[VehicleRequestItem]):
    # Validate small constraints quickly
    input_list = [r.dict() for r in request]
    total_qty = sum(r["quantity"] for r in input_list)
    if total_qty == 0:
        raise HTTPException(status_code=400, detail="No vehicles requested.")
    if total_qty > 5:
        raise HTTPException(status_code=400, detail="Total quantity must be <= 5.")

    vehicles = expand_vehicles(input_list)  # list of lengths
    # Sort vehicles in descending order to improve speed
    vehicles_sorted = sorted(vehicles, reverse=True)

    results = []

    # Iterate over locations
    for location_id, listings in LISTINGS_BY_LOCATION.items():
        # For search performance, if the total area capacity across listings is insufficient, skip
        total_cells_available = sum((l["length"] // 10) * (l["width"] // 10) for l in listings)
        total_vehicle_cells_needed = sum(L // 10 for L in vehicles_sorted)
        if total_cells_available < total_vehicle_cells_needed:
            continue

        best_for_location = None

        # To limit combinatorial explosion, only try combinations up to min(#listings, total_qty)
        max_comb_size = min(len(listings), total_qty)
        # sort listings by price to parse cheaper combinations first
        listings_sorted = sorted(listings, key=lambda x: x["price_in_cents"])

        # Pre-generate combinations
        for r in range(1, max_comb_size + 1):
            for combo in itertools.combinations(listings_sorted, r):
                combo_ids = [c["id"] for c in combo]
                combo_price = sum(c["price_in_cents"] for c in combo)

                # If we already have a better solution for this location, skip combos pricier than best
                if best_for_location and combo_price >= best_for_location[0]:
                    continue

                # Aassign each vehicle to one of the listings in combo.
                # Recursion over vehicles, assigning them to listings, collecting assigned lists
                assigned = [[] for _ in combo]
                success = False

                # Simple variable ordering. vehicles_sorted by largest first
                def assign_vehicle(idx: int) -> bool:
                    nonlocal assigned, combo
                    if idx == len(vehicles_sorted):
                        # check that each listing can pack its assigned
                        for li, listing in enumerate(combo):
                            if not listing_can_fit_assigned(listing, assigned[li]):
                                return False
                        return True

                    vlen = vehicles_sorted[idx]
                    # Try each listing in order (cheapest-first helps find cheaper packing early)
                    for li, listing in enumerate(combo):
                        assigned[li].append(vlen)
                        # quick prune
                        if listing_can_fit_assigned(listing, assigned[li]):
                            if assign_vehicle(idx + 1):
                                return True
                        assigned[li].pop()
                    return False

                success = assign_vehicle(0)
                if success:
                    # Feasible packing with this combo
                    if (best_for_location is None) or (combo_price < best_for_location[0]):
                        best_for_location = (combo_price, combo_ids)

        # If best price then break. Continue for all small r
        if best_for_location:
            price, listing_ids = best_for_location
            results.append({
                "location_id": location_id,
                "listing_ids": listing_ids,
                "total_price_in_cents": price
            })

    # Sort by price ascending
    results_sorted = sorted(results, key=lambda x: x["total_price_in_cents"])
    return results_sorted
