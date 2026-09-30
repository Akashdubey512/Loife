"""
reServe AI - Production Route Optimization & CVRP Engine (Phase 11)

Solves Capacitated Vehicle Routing Problems (CVRP / CVRPTW):
1. Single/Multi-stop dynamic route dispatch with 2-Opt local search refinement.
2. Standard CVRPLIB-compliant heuristic solver with Clarke-Wright savings + 2-Opt.
3. Backward-compatible greedy nearest-neighbor solver.

Classification: Combinatorial Optimization Engine (Heuristic Algorithms).
NOT trained machine learning.
"""

import math
import time
from typing import Dict, Any, List, Tuple, Optional
from logistics.optimizer import VehicleRoutingOptimizer


def euclidean_distance(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
    """Standard TSPLIB integer-rounded Euclidean distance (EUC_2D)."""
    dx = c1[0] - c2[0]
    dy = c1[1] - c2[1]
    return round(math.sqrt(dx * dx + dy * dy))


def route_distance(route: List[int], coords: List[Tuple[float, float]], depot: Tuple[float, float]) -> float:
    """Calculates total closed-loop Euclidean distance (depot -> route -> depot)."""
    if not route:
        return 0.0
    d = euclidean_distance(depot, coords[route[0]])
    for i in range(len(route) - 1):
        d += euclidean_distance(coords[route[i]], coords[route[i + 1]])
    d += euclidean_distance(coords[route[-1]], depot)
    return d


def apply_2opt(route: List[int], coords: List[Tuple[float, float]], depot: Tuple[float, float]) -> List[int]:
    """Applies iterative 2-opt local search to eliminate route crossings and minimize distance."""
    best = list(route)
    improved = True
    while improved:
        improved = False
        best_cost = route_distance(best, coords, depot)
        n = len(best)
        for i in range(n - 1):
            for j in range(i + 1, n):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                cost = route_distance(candidate, coords, depot)
                if cost < best_cost:
                    best = candidate
                    best_cost = cost
                    improved = True
                    break
            if improved:
                break
    return best


def solve_cvrp_greedy(instance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Baseline greedy nearest-neighbor heuristic with capacity constraints.
    """
    coords = instance["node_coord"]
    demands = instance["demand"]
    capacity = instance["capacity"]
    dimension = instance["dimension"]
    depot_idx = 0
    depot_coord = coords[depot_idx]

    unvisited = set(range(1, dimension))
    routes = []
    total_distance = 0.0
    t0 = time.perf_counter()

    while unvisited:
        current_route = []
        current_loc = depot_coord
        current_load = 0

        while True:
            best_candidate = None
            best_dist = float("inf")

            for cust_idx in unvisited:
                demand = demands[cust_idx]
                if current_load + demand <= capacity:
                    dist = euclidean_distance(current_loc, coords[cust_idx])
                    if dist < best_dist:
                        best_dist = dist
                        best_candidate = cust_idx

            if best_candidate is not None:
                current_route.append(best_candidate)
                total_distance += best_dist
                current_load += demands[best_candidate]
                current_loc = coords[best_candidate]
                unvisited.remove(best_candidate)
            else:
                dist_to_depot = euclidean_distance(current_loc, depot_coord)
                total_distance += dist_to_depot
                break

        routes.append(current_route)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    visited_all = (sum(len(r) for r in routes) == (dimension - 1))
    capacity_violations = sum(1 for r in routes if sum(demands[c] for c in r) > capacity)
    is_feasible = visited_all and (capacity_violations == 0)

    return {
        "routes": routes,
        "total_distance": round(total_distance, 2),
        "vehicle_count": len(routes),
        "runtime_ms": round(elapsed_ms, 2),
        "is_feasible": is_feasible,
        "capacity_violations": capacity_violations,
        "solver_method": "greedy-nearest-neighbor",
    }


def solve_cvrp_clarke_wright_2opt(instance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Improved deterministic Clarke-Wright Savings heuristic combined with
    intra-route 2-Opt local search refinement.
    Guarantees 100% capacity feasibility and significantly reduces distance gap vs BKS.
    """
    coords = instance["node_coord"]
    demands = instance["demand"]
    capacity = instance["capacity"]
    dimension = instance["dimension"]
    depot_idx = 0
    depot_coord = coords[depot_idx]

    t0 = time.perf_counter()

    # 1. Compute pairwise savings: s_{ij} = d(0, i) + d(0, j) - d(i, j)
    savings = []
    for i in range(1, dimension):
        for j in range(i + 1, dimension):
            s = (euclidean_distance(depot_coord, coords[i]) +
                 euclidean_distance(depot_coord, coords[j]) -
                 euclidean_distance(coords[i], coords[j]))
            savings.append((s, i, j))
    savings.sort(key=lambda x: x[0], reverse=True)

    # 2. Initialize each customer in an independent route: Depot -> i -> Depot
    routes: Dict[int, List[int]] = {i: [i] for i in range(1, dimension)}
    route_loads: Dict[int, int] = {i: demands[i] for i in range(1, dimension)}
    cust_to_route: Dict[int, int] = {i: i for i in range(1, dimension)}

    # 3. Iteratively merge routes according to descending savings while strictly adhering to capacity
    for s, i, j in savings:
        r_i = cust_to_route[i]
        r_j = cust_to_route[j]
        if r_i == r_j:
            continue

        route_i = routes[r_i]
        route_j = routes[r_j]

        # Strict capacity check
        if route_loads[r_i] + route_loads[r_j] > capacity:
            continue

        # Feasible merge configurations (exterior nodes only)
        if route_i[-1] == i and route_j[0] == j:
            merged = route_i + route_j
        elif route_j[-1] == j and route_i[0] == i:
            merged = route_j + route_i
        elif route_i[-1] == i and route_j[-1] == j:
            merged = route_i + route_j[::-1]
        elif route_i[0] == i and route_j[0] == j:
            merged = route_i[::-1] + route_j
        else:
            continue

        routes[r_i] = merged
        route_loads[r_i] += route_loads[r_j]
        for c in route_j:
            cust_to_route[c] = r_i
        del routes[r_j]
        del route_loads[r_j]

    raw_routes = list(routes.values())

    # 4. Intra-route 2-Opt local search refinement on each vehicle route
    optimized_routes = [apply_2opt(r, coords, depot_coord) for r in raw_routes]
    total_distance = sum(route_distance(r, coords, depot_coord) for r in optimized_routes)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # 5. Strict feasibility verification
    visited_all = (sum(len(r) for r in optimized_routes) == (dimension - 1))
    capacity_violations = sum(1 for r in optimized_routes if sum(demands[c] for c in r) > capacity)
    is_feasible = visited_all and (capacity_violations == 0)

    return {
        "routes": optimized_routes,
        "total_distance": round(total_distance, 2),
        "vehicle_count": len(optimized_routes),
        "runtime_ms": round(elapsed_ms, 2),
        "is_feasible": is_feasible,
        "capacity_violations": capacity_violations,
        "solver_method": "clarke-wright-savings-2opt",
    }


def solve_cvrp(instance: Dict[str, Any], method: str = "clarke_wright_2opt") -> Dict[str, Any]:
    """Public solver interface dispatching to the requested heuristic."""
    if method == "clarke_wright_2opt":
        return solve_cvrp_clarke_wright_2opt(instance)
    elif method == "greedy":
        return solve_cvrp_greedy(instance)
    else:
        raise ValueError(f"Unknown CVRP solver method: {method}")


class VehicleRoutingEngine(VehicleRoutingOptimizer):
    """
    Unified high-level routing engine combining dispatch planning
    and benchmark solver algorithms.
    """
    pass


routing_engine = VehicleRoutingEngine()
