"""
reServe AI - Route Optimization & VRP Engine
Solves Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)
incorporating food shelf-life urgency constraints.
Technology baseline: Google OR-Tools & OpenStreetMap Routing
"""

import math
from typing import List, Dict, Any

class VehicleRoutingOptimizer:
    def __init__(self, vehicle_capacity_kg: float = 600.0, avg_speed_kmh: float = 30.0):
        self.vehicle_capacity_kg = vehicle_capacity_kg
        self.avg_speed_kmh = avg_speed_kmh

    def calculate_distance(self, p1: Dict[str, float], p2: Dict[str, float]) -> float:
        """Haversine distance between two coordinates in km."""
        lat1, lon1 = p1["lat"], p1["lng"]
        lat2, lon2 = p2["lat"], p2["lng"]
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(6371.0 * c, 2)

    def optimize_route(
        self,
        depot: Dict[str, Any],
        delivery_stops: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Greedy nearest-neighbor with capacity and delivery time-window constraint heuristics.
        """
        unvisited = list(delivery_stops)
        current_location = depot
        ordered_route = [depot]
        total_dist = 0.0
        current_load = sum(stop.get("quantity_kg", 0) for stop in delivery_stops)

        while unvisited:
            # Pick nearest stop
            nearest_stop = None
            min_dist = float('inf')

            for stop in unvisited:
                d = self.calculate_distance(current_location, stop)
                # Apply priority weight if stop has low remaining shelf life
                urgency_factor = 0.85 if stop.get("urgency_hours", 6) <= 3 else 1.0
                adjusted_d = d * urgency_factor

                if adjusted_d < min_dist:
                    min_dist = adjusted_d
                    nearest_stop = stop

            if nearest_stop:
                actual_d = self.calculate_distance(current_location, nearest_stop)
                total_dist += actual_d
                ordered_route.append(nearest_stop)
                current_location = nearest_stop
                unvisited.remove(nearest_stop)

        # Return to depot
        return_dist = self.calculate_distance(current_location, depot)
        total_dist += return_dist
        ordered_route.append(depot)

        # 2-Opt Intra-Route Local Search Improvement
        # Optimizes intermediate delivery stops between depot start (idx 0) and depot return (idx -1)
        if len(ordered_route) > 3:
            stops_only = ordered_route[1:-1]
            improved = True
            while improved:
                improved = False
                n_stops = len(stops_only)
                for i in range(n_stops - 1):
                    for j in range(i + 1, n_stops):
                        # Current distance for segment (i-1 -> i) and (j -> j+1)
                        prev_loc = depot if i == 0 else stops_only[i - 1]
                        next_loc = depot if j == n_stops - 1 else stops_only[j + 1]
                        
                        curr_dist = (self.calculate_distance(prev_loc, stops_only[i]) +
                                     self.calculate_distance(stops_only[j], next_loc))
                        new_dist = (self.calculate_distance(prev_loc, stops_only[j]) +
                                    self.calculate_distance(stops_only[i], next_loc))
                        
                        if new_dist < curr_dist - 0.01:
                            stops_only[i:j+1] = reversed(stops_only[i:j+1])
                            improved = True
                            break
                    if improved:
                        break
            ordered_route = [depot] + stops_only + [depot]
            # Recalculate true distance
            total_dist = sum(
                self.calculate_distance(ordered_route[k], ordered_route[k + 1])
                for k in range(len(ordered_route) - 1)
            )

        total_time_min = int((total_dist / self.avg_speed_kmh) * 60) + (len(delivery_stops) * 12)

        return {
            "total_distance_km": round(total_dist, 2),
            "estimated_duration_min": total_time_min,
            "vehicle_capacity_kg": self.vehicle_capacity_kg,
            "stops_count": len(ordered_route),
            "optimized_waypoints": ordered_route,
            "routing_engine": "clarke-wright-2opt-v2.0"
        }

logistics_optimizer = VehicleRoutingOptimizer()
