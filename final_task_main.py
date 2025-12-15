import heapq
from collections import defaultdict

def parse_input(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]
    
    cities = {}
    roads = []
    requests = []
    
    section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line == '[CITIES]':
            section = 'CITIES'
        elif line == '[ROADS]':
            section = 'ROADS'
        elif line == '[REQUESTS]':
            section = 'REQUESTS'
        elif section == 'CITIES':
            if ':' in line:
                parts = line.split(':', 1)
                city_id = int(parts[0].strip())
                city_name = parts[1].strip()
                cities[city_name] = city_id
        elif section == 'ROADS':
            if '-' in line:
                parts = line.split(':', 1)
                road_info = parts[1].strip()
                cities_part = parts[0].strip()
                
                city_ids = cities_part.split('-')
                city1_id = int(city_ids[0].strip())
                city2_id = int(city_ids[1].strip())
                
                params = [int(p.strip()) for p in road_info.split(',')]
                length, time, cost = params
                
                roads.append((city1_id, city2_id, length, time, cost))
        elif section == 'REQUESTS':
            if '->' in line:
                parts = line.split('|')
                route_part = parts[0].strip()
                priority_part = parts[1].strip() if len(parts) > 1 else ''
                
                cities_part = route_part.split('->')
                city_from = cities_part[0].strip()
                city_to = cities_part[1].strip()
                
                priorities = []
                if priority_part:
                    priorities_str = priority_part.strip('()')
                    priorities = [p.strip() for p in priorities_str.split(',')]
                
                requests.append((city_from, city_to, priorities))
    
    return cities, roads, requests


def build_graph(roads):
    graph = defaultdict(list)
    
    for city1, city2, length, time, cost in roads:
        graph[city1].append((city2, length, time, cost))
        graph[city2].append((city1, length, time, cost))
    
    return graph



def dijkstra_with_full_priority_fixed(graph, start, target, main_criterion):
    if main_criterion == 0: 
        compare_order = [0, 1, 2]  # Д,В,С
    elif main_criterion == 1:
        compare_order = [1, 0, 2]  # В,Д,С  
    else:
        compare_order = [2, 0, 1]  # С,Д,В
    
    best_values = {city: [float('inf'), float('inf'), float('inf')] for city in graph}
    best_values[start] = [0, 0, 0]
    previous = {city: None for city in graph}
    
    
    pq = [(0, start)]  
    
    while pq:
        current_main_weight, current_city = heapq.heappop(pq)
        
        if current_city == target:
            break
        
        current_values = best_values[current_city]
        
        for neighbor, length, time, cost in graph[current_city]:
            new_values = [
                current_values[0] + length,
                current_values[1] + time,
                current_values[2] + cost
            ]
            
            if main_criterion == 0:
                new_main_weight = new_values[0]
            elif main_criterion == 1:
                new_main_weight = new_values[1]
            else:
                new_main_weight = new_values[2]
            
            old_values = best_values[neighbor]
            
            is_better = False
            for criterion_idx in compare_order:
                if new_values[criterion_idx] < old_values[criterion_idx]:
                    is_better = True
                    break
                elif new_values[criterion_idx] > old_values[criterion_idx]:
                    break

            if is_better:
                best_values[neighbor] = new_values
                previous[neighbor] = current_city
                
                heapq.heappush(pq, (new_main_weight, neighbor))
    
    if previous[target] is None and start != target:
        return None, None, None, None, None
    
    path = []
    current = target
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    
    final_values = best_values[target]
    return path, final_values[0], final_values[1], final_values[2], None


def find_best_route_by_criteria(graph, start_city_id, target_city_id, criterion_idx, id_to_name):
    path, length, time, cost, _ = dijkstra_with_full_priority_fixed(graph, start_city_id, target_city_id, criterion_idx)
    
    if path is None:
        return None
    
    path_names = [id_to_name[city_id] for city_id in path]
    
    return {
        'path': path_names,
        'length': length,
        'time': time,
        'cost': cost
    }


def get_route_string(route, criterion_name):
    if route is None:
        return f"{criterion_name}: Маршрут не найден"
    
    path_str = ' -> '.join(route['path'])
    return f"{criterion_name}: {path_str} | Д={route['length']}, В={route['time']}, С={route['cost']}"


def find_all_routes_dfs(graph, start, target, visited, current_path, all_routes, current_length, current_time, current_cost, max_routes=10):
    if len(all_routes) >= max_routes:
        return
    
    visited[start] = True
    current_path.append(start)
    
    if start == target:
        all_routes.append({
            'path': current_path.copy(),
            'length': current_length,
            'time': current_time,
            'cost': current_cost
        })
    else:
        for neighbor, length, time, cost in graph[start]:
            if not visited[neighbor]:
                find_all_routes_dfs(graph, neighbor, target, visited, current_path, all_routes,
                                  current_length + length, current_time + time, current_cost + cost,
                                  max_routes)
    
    current_path.pop()
    visited[start] = False


def find_compromise_route(best_routes, priorities, id_to_name, graph, start_city_id, target_city_id):
    if not priorities:
        return None
    
    priority_to_idx = {'Д': 0, 'В': 1, 'С': 2}
    priority_indices = [priority_to_idx[p] for p in priorities]
    
    idx_to_param = {0: 'length', 1: 'time', 2: 'cost'}
    
    valid_routes = [r for r in best_routes if r is not None]
    
    if not valid_routes:
        return None
    
    def get_priority_values(route):
        values = []
        for idx in priority_indices:
            param_name = idx_to_param[idx]
            values.append(route[param_name])
        return tuple(values)
    
    valid_routes.sort(key=lambda r: get_priority_values(r))
    
    return valid_routes[0]


def main():
    cities, roads, requests = parse_input('input.txt')
    
    id_to_name = {v: k for k, v in cities.items()}
    graph = build_graph(roads)
    
    results = []
    
    for city_from_name, city_to_name, priorities in requests:
        if city_from_name not in cities or city_to_name not in cities:
            results.append("ДЛИНА: Маршрут не найден")
            results.append("ВРЕМЯ: Маршрут не найден")
            results.append("СТОИМОСТЬ: Маршрут не найден")
            results.append("КОМПРОМИСС: Маршрут не найден")
            results.append("")
            continue
        
        start_city_id = cities[city_from_name]
        target_city_id = cities[city_to_name]
        
        best_routes = []
        criterion_names = ['ДЛИНА', 'ВРЕМЯ', 'СТОИМОСТЬ']
        
        for i in range(3):
            route = find_best_route_by_criteria(graph, start_city_id, target_city_id, i, id_to_name)
            best_routes.append(route)
            results.append(get_route_string(route, criterion_names[i]))
        
        compromise_route = None
        if priorities:
            compromise_route = find_compromise_route(best_routes, priorities, id_to_name, 
                                                   graph, start_city_id, target_city_id)
        
        if compromise_route:
            path_str = ' -> '.join(compromise_route['path'])
            results.append(f"КОМПРОМИСС: {path_str} | Д={compromise_route['length']}, В={compromise_route['time']}, С={compromise_route['cost']}")
        else:
            results.append("КОМПРОМИСС: Маршрут не найден")
        
        results.append("")
    
    with open('output.txt', 'w', encoding='utf-8') as f:
        for result in results:
            f.write(result + '\n')
    
    for result in results:
        print(result)


if __name__ == "__main__":
    main()