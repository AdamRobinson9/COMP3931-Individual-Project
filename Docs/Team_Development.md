# Team Play Update

In the first prototypes, each team had only one player, which was moved either by defending or attacking based on the distances from their targets.

This was the first stage of AI agent implementation but it lacked strategical depth, which is a feature of teams containing multiple players.

## Creating teams
The first stage to increasing team sizes is to create an array of players, as shown, instead of a single player instance.
```
red_positions = positions(graph, red_base, num_players)
blue_positions = positions(graph, blue_base, num_players)
# Initialise players
for position in red_positions:
    red_players.append(Player("red", start_node=position, base_node=red_base))
for position in blue_positions:
    blue_players.append(Player("blue", start_node=position, base_node=blue_base))
```
We must also decide on positions for each of the players to start on, instead of the single player starting on the base node each time. To do this we can use a BFS search to surround the team's base node with its players.
```
def positions(graph, base, num_players):
    """Use a BFS to surround the team's base node with the specified number of players"""
    visited = set()
    queue = deque([base])
    order = []

    # Explore nodes until we run out, or have enough positions
    while queue and len(order)<num_players:
        # Explore next node
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            order.append(node)
            # Add neighbours to queue if not already visited
            for neighbour in graph.neighbors(node):
                if neighbour not in visited:
                    queue.append(neighbour)

    return order
```
## Heuristic adaptation
Since the previous heuristic functions (`shortest_path_move`, `defensive_move` and `balanced_move`) had been designed for a single player team, there were small tweaks required, making them suitable for multiple player teams.
### Player selection
Originally, the methods was able to directly retrieve the current player from the game state:
```
current_player = self.get_current_player(state)
```
This worked since there was only 1 possible player to move per turn. However, with multiple players available to move, the functions must calculate the move for each of the players seperately. This is done by passing the player to move as a parameter instead.
```
def shortest_path_move(self, graph, state, current_player):
```
### Team aware decision making
The original heuristics only considered the single player and its one opponent to find its target.
```
opposition_player = self.get_opposition_player(state)
        # First check if the opposition player has your flag
        if opposition_player.has_enemy_flag:
```
However, with multiple players in the opposition theam, these functions must now check each of the opposition players to find which is the best move to take.
```
opposition_players = self.get_opposition_players(state)
        flag_carrier = None
        # Find the player (if any) that is carrying the flag
        for opposition_player in opposition_players:
            if opposition_player.has_enemy_flag:
                flag_carrier = opposition_player
```
### Target selection
Previously, it was straightforward to decide on the players target, based only on whether the player was carrying the flag or not.
```
# If the current player has the enemy flag, then...
        if current_player.has_enemy_flag == True:
            target = current_player.base_node   # ...move towards the base node
        # If the current player doesn't have the enemy flag, then...
        else:
            # ... move towards enemy's flag
```
In the updated version, another player on the team could be carrying the flag. This means that even though the player is not carrying the flag, there is no need to target it because another player on the team is already returning it to base.
```
if current_player.has_enemy_flag == True:
            target = current_player.base_node   # ...move towards the base node
        # If another team member has the flag, then...
        elif enemy_flag.carried_by is not None:
            # ...check if the team's flag is carried
            if current_player.get_current_flag(state).carried_by != None:
                 target = current_player.get_current_flag(state).position   # defend the flag if carried by an enemy
            else:
                target = current_player.base_node   # protect the base if flag isn't carried
        # If nobody has the enemy flag, then...
        else:
            # ...move towards the enemy's flag
```
This gives the player more priorities depending on the different game situations that could arise.

## Team based decision making
Since we now have multiple players to move, but only one player is able to move per turn, we need to find a way of deciding which player's move is the most beneficial to the team.

### Shortest path
Originally, the approach was to calculate the path for each player using `balanced_move` and choose the player that has the shortest path to their target.
```
def player_to_move(self):
    if self.turn == "red":
        players = self.red
    else:
        players = self.blue
        
    choice = None
    shortest_path = self.graph.number_of_edges()
    for player in players:
        path = player.balanced_move(self.graph, self, player)
        print (player.position, ", ", len(path))
        if (len(path) < shortest_path and len(path) > 1):
            choice = player
            shortest_path = len(path)
    return choice
```
### Score evaluation
After testing this approach, it was clear that the moves chosen were often not beneficial to the team and a new method was required to evaluate the risks posed by the opposition team and avoid them, even if it isn't immediately the simplest option.
```
def player_to_move(self):
    """Select the player whose move is the most benificial."""
    if self.turn == "red":
        players = self.red
        current_flag = self.red_flag
        enemy_flag = self.blue_flag
        enemy_base = self.blue_base
    else:
        players = self.blue
        current_flag = self.blue_flag
        enemy_flag = self.red_flag
        enemy_base = self.red_base

    best_player = None
    best_score = float("-inf")

    # For each player, calculate how beneficial a move is
    for player in players:
        path = player.balanced_move(self.graph, self, player)
        if len(path) <= 1:
            continue

        score = 0

        # Record how much closer the move brings the player to its target
        target = player.base_node if player.has_enemy_flag else enemy_flag.position
        old_distance = len(nx.shortest_path(self.graph, player.position, target))
        new_distance = len(nx.shortest_path(self.graph, path[1], target))
        score += (old_distance - new_distance) + 1 / (1 + new_distance)

        # Penalise moves if they cluster with team mates
        team_positions = []
        for p in players:
            if p != player:
                team_positions.append(p.position)
        if path[1] in team_positions:
            score = 0.8*score

        # Reward moves if they reduce distance to team's flag, if it's stolen
        current_flag = self.red_flag if self.turn == "red" else self.blue_flag
        if current_flag.carried_by is not None:
            distance_to_flag = len(nx.shortest_path(self.graph, path[1], current_flag.position))
            total_distance = len(nx.shortest_path(self.graph, current_flag.base_node, enemy_base))
            opp_distance_home = len(nx.shortest_path(self.graph, current_flag.position, enemy_base))
            base_proximity = total_distance/opp_distance_home

            score += base_proximity / (1 + distance_to_flag)  # closer to flag = higher score

        # Keep the best-scoring player
        if score > best_score:
            best_score = score
            best_player = player

    # Penalise moves that enter the striking distance of opponents
        threat_nodes = set()
        for enemy in enemy_players:
            threat_nodes.add(enemy.position)
            threat_nodes.update(self.graph.neighbors(enemy.position))

        if path[1] in threat_nodes:
            score = score*0.7  # Penalty for moving within striking distance

        # Stronger penalty if carrying enemy flag 
        if player.has_enemy_flag and path[1] in threat_nodes:
            score = score*0.5

        # Keep the best-scoring player
        if score > best_score:
            best_score = score
            best_player = player

    # If there is a best option, return it
    if best_player:
        return best_player
    # Return a random player if no best option was found
    else:
        return random.choice(players)
```
This method calculates a score for each move, balancing:
- The progress towards its goal,
- Avoiding clustering of the team mates, and
- The ability to recognise and prevent opponents from capturing the teams's flag.

This approach allows the teams to coordiate their movement, allowing them to make intelligent moves towards winning the game.