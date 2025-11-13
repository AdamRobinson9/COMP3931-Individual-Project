# FILE:         Prototype3-Teams.py
# AUTHOR:       Adam Robinson
# DATE:         08/11/2025
# DESCRIPTION:  Adding the capability to add multiple players to teach team.
#               Implemented a team array to store all of the players for each team, instead of one single player.
#               Updated the game logic for one player to move per turn and check the movement against all players.

from collections import deque
import random
import time
import networkx as nx
import matplotlib.pyplot as plt
plt.ion()

class Flag:
    def __init__(self, team, base_node):
        self.team = team  # red or blue
        self.base_node = base_node
        self.position = base_node
        self.carried_by = None

    def reset(self):
        """Return flag to base"""
        self.position = self.base_node
        self.carried_by = None

    def pick_up(self, player):
        """Let player pick up flag"""
        self.carried_by = player
        player.has_enemy_flag = True

    def is_captured(self):
        """Check if flag has been captured"""
        if self.carried_by is None:
            return False
        else:
            return self.carried_by.position == self.carried_by.base_node
        
class Player:
    def __init__(self, team, start_node, base_node):
        self.team = team  # red or blue
        self.position = start_node
        self.base_node = base_node
        self.has_enemy_flag = False

    def move(self, graph, state):
        """Move player"""
        path = self.balanced_move(graph, state, self)
        if len(path)>1:
            self.position = path[1]
        else:
            self.position = self.random_move(graph) # If no optimal move was caluclated

    def random_move(self, graph):
        """Pick a random available move"""
        return random.choice(list(graph.neighbors(self.position)))
        
    def get_opposition_players(self, state):
        """Return the team who's turn it is not"""
        if self.team == "red":
            return state.blue
        else:
            return state.red
        
    def get_current_flag(self, state):
        """Return the current team's flag"""
        if self.team == "red":
            return state.red_flag
        else:
            return state.blue_flag
        
    def get_enemy_flag(self, state):
        """Return the opponent's flag"""
        if self.team == "red":
            return state.blue_flag
        else:
            return state.red_flag
        
    def is_safe(self, state):
        """Decide whether the player is in a safe zone (either base node)"""
        return self.position == state.red_base or self.position == state.blue_base
        
    def shortest_path_move(self, graph, state, current_player):
        """Return the next node in the shortest path to the player's target (flag/base)"""
        enemy_flag = self.get_enemy_flag(state)
        # If the current player has the enemy flag, then...
        if current_player.has_enemy_flag == True:
            target = current_player.base_node   # ...move towards the base node
        # If another team member has the flag, then...
        elif enemy_flag.carried_by is not None:
            # ...check if the team's flag is carried
            if current_player.get_current_flag(state).carried_by != None:
                 target = current_player.get_current_flag(state).position   # defend flag if it is carried by an enemy
            else:
                target = current_player.base_node   # protect the base if flag isn't carried
        # If nobody has the enemy flag, then...
        else:
            if self.team == "red":
                target = state.blue_flag.position   # ...move towards the enemy's flag
            else:
                target = state.red_flag.position    # ...move towards the enemy's flag
        # Return the shortest path to the target
        path = nx.shortest_path(graph, current_player.position, target)
        return path

    def defensive_move(self, graph, state, current_player):
        """Return the next move in an attempt to block the opponent if they have a flag, otherwise move to capture the flag"""
        opposition_players = self.get_opposition_players(state)
        flag_carrier = None
        # Find the player (if any) that is carrying the flag
        for opposition_player in opposition_players:
            if opposition_player.has_enemy_flag:
                flag_carrier = opposition_player

        # First check if an opposition player has your flag
        if flag_carrier != None:
            # 'Intercept' the opponent if they are directly within range
            if flag_carrier.position in graph.neighbors(current_player.position):
                return [current_player.position, flag_carrier.position]
            # If the opponent is not in range...
            else:
                # ...then block the opponents path to return the flag
                opposition_path = nx.shortest_path(graph, flag_carrier.position, flag_carrier.base_node)
                target = opposition_path[int(len(opposition_path)/2)]   # Aim for the center of the opponent's path back 
                path = nx.shortest_path(graph, current_player.position, target)
                # If player is already in the center of the path, move closer to the opponent
                if target == current_player.position:
                    path = nx.shortest_path(graph, current_player.position, flag_carrier.position)
                return path
        # If the opponent isn't carrying the team's flag, aim to capture their flag.
        else:
            return self.shortest_path_move(graph, state, current_player)
        
    def balanced_move(self, graph, state, current_player):
        """Consider game situation to decide whether to attack or defend"""
        opposition_players = self.get_opposition_players(state)
        current_flag = self.get_current_flag(state)
        enemy_flag = self.get_enemy_flag(state)

        # Find the target for the player depending on who has a flag
        if enemy_flag.carried_by is not None :
            player_target = current_flag.position
        elif current_player.has_enemy_flag == True:
            player_target = current_player.base_node
        else:
            player_target = enemy_flag.position
        
        # Find which of the players is closest to their target
        min_opposition_distance = float('inf')
        for opposition_player in opposition_players:
            # Find the target for the opponent depending on whether they have a flag
            if opposition_player.has_enemy_flag == True:
                opposition_target = opposition_player.base_node
            else:
                opposition_target = current_flag.position

            # Calculate the distance from the target and decide if it is the closest on the team
            opposition_distance = len(nx.shortest_path(graph, opposition_player.position, opposition_target))
            if opposition_distance < min_opposition_distance:
                min_opposition_distance = opposition_distance

        # Calcuate the distance from the current player to their target
        player_distance = len(nx.shortest_path(graph, current_player.position, player_target))
        # If the player is closer to its target than the opponents...
        if player_distance <= min_opposition_distance:
            return self.shortest_path_move(graph, state, current_player)    # ...attack
        # If the opponent is closer to its target than the player...
        else:
            return self.defensive_move(graph, state, current_player) # ...defend
        
class GameState:
    def __init__(self, graph, red_players, blue_players, red_flag, blue_flag, red_base, blue_base):
        self.graph = graph
        self.red = red_players
        self.blue = blue_players
        self.red_flag = red_flag
        self.blue_flag = blue_flag
        self.red_base = red_base
        self.blue_base = blue_base
        self.turn = "red"
        self.winner = None
        self.turn_count = 0

    def switch_turn(self):
        """Change the player at the end of a turn"""
        if self.turn == "red":
            self.turn = "blue"
        else:
            self.turn = "red"

    def check_movement(self, player):
        """Ensure the correct rules are applied based on player movements"""
        if self.turn == "red":
            returning_flag = self.red_flag
            # Check all opponents to see if they're carrying flag and a player has intercepted
            for blue_player in self.blue:
                if player.position == blue_player.position:
                    # If a player has intercepted and opponent is not in a safe zone, then reset flag
                    if returning_flag.carried_by == blue_player and blue_player.is_safe(self) == False:
                        returning_flag.reset()
                        blue_player.has_enemy_flag = False
            # Pick up the flag from its base
            if player.position == self.blue_flag.position and self.blue_flag.carried_by is None:
                self.blue_flag.pick_up(player)    
        else:
            returning_flag = self.blue_flag
            # Check all opponents to see if they're carrying flag and a player has intercepted
            for red_player in self.red:
                if player.position == red_player.position:
                    # If a player has intercepted and opponent is not in a safe zone, then reset flag
                    if returning_flag.carried_by == red_player and red_player.is_safe(self) == False:
                        returning_flag.reset()
                        red_player.has_enemy_flag = False
            # Pick up the flag from its base
            if player.position == self.red_flag.position and self.red_flag.carried_by is None:
                self.red_flag.pick_up(player)

        # Update flag position to follow its carrier
        if self.red_flag.carried_by is not None:
            self.red_flag.position = self.red_flag.carried_by.position
        if self.blue_flag.carried_by is not None:
            self.blue_flag.position = self.blue_flag.carried_by.position

    def player_to_move(self):
        """Select the player whose move is the most benificial."""
        if self.turn == "red":
            players = self.red
            enemy_players = self.blue
            current_flag = self.red_flag
            enemy_flag = self.blue_flag
            enemy_base = self.blue_base
        else:
            players = self.blue
            enemy_players = self.red
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
              

    def check_win(self):
        """Check if either player has captured their opponents flag"""
        if self.red_flag.is_captured():
            self.winner = "Blue"
        elif self.blue_flag.is_captured():
            self.winner = "Red"
        
class CaptureTheFlag:
    def __init__(self, graph, red_player, blue_player, red_flag, blue_flag, red_base, blue_base):
        self.state = GameState(graph, red_player, blue_player, red_flag, blue_flag, red_base, blue_base)
        self.pos = nx.spring_layout(graph, seed=42)

    def draw_graph(self):
        """Show the game state on the graph - for testing"""
        plt.clf() # Clear the existing graph
        nx.draw(self.state.graph, self.pos, with_labels=True) # Draw the updated graph
        # Colour the nodes to show the flag and player positions
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[self.state.red_flag.position], edgecolors="red", linewidths=4)
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[self.state.blue_flag.position], edgecolors="blue", linewidths=4)
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[player.position for player in self.state.red], node_color="pink")
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[player.position for player in self.state.blue], node_color="cyan")
        # Show the updated graph
        plt.show()
        plt.pause(0.2)

    def play(self):
        """Allow the players to move until there is a winner"""
        while self.state.winner is None:
            # Update game state display
            self.draw_graph()
            # Find a player to move, and move them
            player = self.state.player_to_move()          
            player.move(self.state.graph, self.state)
            # Process the move
            self.state.check_movement(player)
            self.state.check_win()
            self.state.switch_turn()
            time.sleep(0.2)
        # Display the winner at the end of the game
        print("WINNER: ", self.state.winner)    

def build_graph():
    """Create the playing graph and label its nodes"""
    # Set the graph topology
    graph = nx.grid_2d_graph(4, 3) 

    # Give each node a numbered label
    labels = {}
    nodes = list(graph.nodes())
    for i in range(len(nodes)):
        labels[nodes[i]] = i
    graph = nx.relabel_nodes(graph, labels)
    
    return graph    

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

def main():
    """Run the game"""
    random.seed(42) # For reproducibility
    # Fix the assests required for the game
    graph = build_graph()
    num_players = 3
    red_players = []
    blue_players = []
    red_base = 0
    blue_base = graph.number_of_nodes()-1
    red_positions = positions(graph, red_base, num_players)
    blue_positions = positions(graph, blue_base, num_players)
    # Initialise players
    for position in red_positions:
        red_players.append(Player("red", start_node=position, base_node=red_base))
    for position in blue_positions:
        blue_players.append(Player("blue", start_node=position, base_node=blue_base))


    # Initialise flags
    red_flag = Flag("red", base_node=0)
    blue_flag = Flag("blue", base_node=graph.number_of_nodes()-1)

    # Initialise and begin the game
    game = CaptureTheFlag(graph, red_players, blue_players, red_flag, blue_flag, red_base, blue_base)
    game.play()

if __name__ == "__main__":
    main()