# Heuristic Strategy Design

We begin to develop AI agents to control the behaviour of the players. We will begin with a basic heuristic and develop the behaviour to build a balanceed attacking and defensive agent.

## Attacking Heuristic - Shortest Path Movement

### Objective
Move directly towards the target node via the shortest possible route. The target is the opponents flag if it is not already carried, otherwise, the target is the team's base node to return the flag.

```
def shortest_path_move(self, graph, state):
    """Return the next node in the shortest path to the player's target (flag/base)"""
    current_player = self.get_current_player(state)
    # If the current player has the enemy flag, then...
    if current_player.has_enemy_flag == True:
        target = current_player.base_node   # ...move towards the base node
    # If the current player doesn't have the enemy flag, then...
    else:
        if state.turn == "red":
            target = state.blue_flag.position   # ...move towards the enemy's flag
        else:
            target = state.red_flag.position    # ...move towards the enemy's flag
    # Return the next node in the shortest path to the target
    path = nx.shortest_path(graph, current_player.position, target)
    return path[1]
```

#### Helper Function
```
def get_current_player(self, state):
    """Return the player who's turn it is"""
    if state.turn == "red":
        return state.red
    else:
        return state.blue
```
This approach always aims for the shortest route to win, a better heuristic should consider the opponents position so the player can defend their flag too.

## Defensive Heuristic

### Objective
Prioritise protecting the team's flag by intercepting the opponent if they are carrying it.

```
def defensive_move(self, graph, state):
    """Return the next move in an attempt to block the opponent if they have a flag, otherwise move to capture the flag"""
    current_player = self.get_current_player(state)
    opposition_player = self.get_opposition_player(state)
    # First check if the opposition player has your flag
    if opposition_player.has_enemy_flag:
        # 'Intercept' the opponent if they are within range
        if opposition_player.position in graph.neighbors(current_player.position):
            return opposition_player.position
        # If the opponent is not in range...
        else:
            # ...then block the opponents path to return the flag
            opposition_path = nx.shortest_path(graph, opposition_player.position, opposition_player.base_node)
            target = opposition_path[int(len(opposition_path)/2)]   # Aim for the center of the opponent's path back 
            path = nx.shortest_path(graph, current_player.position, target)
            # If player is already in the center of the path, move closer to the opponent
            if target == current_player.position:
                path = nx.shortest_path(graph, current_player.position, opposition_player.position)
            return path[1]
    # If the opponent doesnt have a flag, aim to capture their flag.
    else:
        return self.shortest_path_move(graph, state)
```

#### Helper Function
```
def get_opposition_player(self, state):
    """Return the player who's turn it is not"""
    if state.turn == "red":
            return state.blue
    else:
        return state.red
```

This approach focuses primarily on preventing the opponent from capturing a flag, however collecting the opponents flag can provide a greater strategical advantage. A better heuristic may balance these two approaches to switch between attack and defence depending on the game situation.

## Balanced approach

### Objective
Dynamically switch between attacking and defending based on the relative distances between each player and their goals.

```
def balanced_move(self, graph,state):
    current_player = self.get_current_player(state)
    opposition_player = self.get_opposition_player(state)
    current_flag = self.get_current_flag(state)
    opposition_flag = self.get_opposition_flag(state)

    # Find the target for the player depending on whether they have a flag
    if current_player.has_enemy_flag == True:
        player_target = current_player.base_node
    else:
       player_target = opposition_flag.position
        
    # Find the target for the opponent depending on whether they have a flag
    if opposition_player.has_enemy_flag == True:
       opposition_target = opposition_player.base_node
    else:
        opposition_target = current_flag.position

    # Calcuate the distance from the players to their targets
    player_distance = len(nx.shortest_path(graph, current_player.position, player_target))
    opposition_distance = len(nx.shortest_path(graph, opposition_player.position, opposition_target))

    # If the player is closer to its target than the opponent...
    if player_distance <= opposition_distance:
        return self.shortest_path_move(graph, state)    # ...attack
    # If the opponent is closer to its target than the player...
    else:
        return self.defensive_move(graph,state) # ...defend
```

#### Helper Functions
```
def get_current_flag(self, state):
    """Return the current player's flag"""
    if state.turn == "red":
        return state.red_flag
    else:
        return state.blue_flag
        
def get_opposition_flag(self, state):
    """Return the opponent's flag"""
    if state.turn == "red":
       return state.blue_flag
    else:
        return state.red_flag
```

We now have a combined approach balancing attacking and defending strategy. To refine these approaches, we could:
- Adapt the attacking strategy `shortest_path_move` to avoid routes/ moves that puts the player at immediate risk of being intercepted if they have a flag.
- Adapt the defending strategy `defensive_move` to consider every minimal route that the opponent might take, using `networkx.all_shortest_paths`, to calculate the target node as the most common node across all of these paths - forming effectively a minimum cut or chokepoint.
- Introduce a way of deciding whether to attack or defend when the tow teams are equal distance from their targets.