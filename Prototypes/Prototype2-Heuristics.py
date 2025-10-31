# FILE:         Prototype2-Heuristics.py
# AUTHOUR:      Adam Robinson
# DATE:         31/10/2025
# DESCRIPTION:  Updating the initial implementation to remove the human input and allow heuristic-lead gameplay.
#               Added new methods for: random moves, attacking-led moves, defensive lead moves, and dynamic moves.

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
    def __init__(self, team, start_node):
        self.team = team  # red or blue
        self.position = start_node
        self.base_node = start_node
        self.has_enemy_flag = False

    def move(self, graph, state):
        """Move the player"""
        self.position = self.balanced_move(graph, state)

    def random_move(self, graph):
        """Pick a random available move"""
        return random.choice(list(graph.neighbors(self.position)))
    
    def get_current_player(self, state):
        """Return the player who's turn it is"""
        if state.turn == "red":
            return state.red
        else:
            return state.blue
        
    def get_opposition_player(self, state):
        """Return the player who's turn it is not"""
        if state.turn == "red":
            return state.blue
        else:
            return state.red
        
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
        
class GameState:
    def __init__(self, graph, red_player, blue_player, red_flag, blue_flag):
        self.graph = graph
        self.red = red_player
        self.blue = blue_player
        self.red_flag = red_flag
        self.blue_flag = blue_flag
        self.turn = "red"
        self.winner = None
        self.turn_count = 0

    def switch_turn(self):
        """Change the player at the end of a turn"""
        if self.turn == "red":
            self.turn = "blue"
        else:
            self.turn = "red"

    def check_movement(self):
        """Ensure the correct rules are applied based on player movements"""
        # Return carried flag to its base node if the player is caught
        if self.red.position == self.blue.position:
            if self.turn == "red":
                defender = self.blue                # Player carrying the flag
                returning_flag = self.red_flag      # Flag to be returned
            else:
                defender = self.red                 # Player carring the flag
                returning_flag = self.blue_flag     # Flag to be returned
            if returning_flag.carried_by == defender:   # Return flag if it is carried by 'defender'
                returning_flag.reset()
                defender.has_enemy_flag = False

        # Pick up the flag from its base
        if self.red.position == self.blue_flag.position and self.blue_flag.carried_by is None:
            self.blue_flag.pick_up(self.red)
        if self.blue.position == self.red_flag.position and self.red_flag.carried_by is None:
            self.red_flag.pick_up(self.blue)

        # Update flag position to follow its carrier
        if self.red_flag.carried_by is not None:
            self.red_flag.position = self.red_flag.carried_by.position
        if self.blue_flag.carried_by is not None:
            self.blue_flag.position = self.blue_flag.carried_by.position


    def check_win(self):
        """Check if either player has captured their opponents flag"""
        if self.red_flag.is_captured():
            self.winner = "Blue"
        elif self.blue_flag.is_captured():
            self.winner = "Red"
        
class CaptureTheFlag:
    def __init__(self, graph, red_player, blue_player, red_flag, blue_flag):
        self.state = GameState(graph, red_player, blue_player, red_flag, blue_flag)
        self.pos = nx.spring_layout(graph, seed=42)

    def draw_graph(self):
        """Show the game state on the graph"""
        plt.clf() # Clear the existing graph
        nx.draw(self.state.graph, self.pos, with_labels=True) # Draw the updated graph
        # Colour the nodes to show the flag and player positions
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[self.state.red_flag.position], edgecolors="red", linewidths=4)
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[self.state.blue_flag.position], edgecolors="blue", linewidths=4)
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[self.state.red.position], node_color="pink")
        nx.draw_networkx_nodes(self.state.graph, self.pos, nodelist=[self.state.blue.position], node_color="cyan")
        # Show the updated graph
        plt.show()
        plt.pause(1)

    def play(self):
        """Allow the players to move until there is a winner"""
        while self.state.winner is None:
            if self.state.turn == "red":
                player = self.state.red
            else:
                player = self.state.blue
            # Update game state details
            self.draw_graph()
            print("Current turn: ", self.state.turn)
            print("Available moves: ", list(self.state.graph.neighbors(player.position)))
            player.move(self.state.graph, self.state)
            
            # Process the move
            self.state.check_movement()
            self.state.check_win()
            self.state.switch_turn()
            time.sleep(1)
        
        print("WINNER: ", self.state.winner)    # Display the winner at the end of the game

def build_graph():
    """Create the playing graph and label its nodes"""
    graph = nx.grid_2d_graph(3, 3) 

    # Give each node a numbered label
    labels = {}
    nodes = list(graph.nodes())
    for i in range(len(nodes)):
        labels[nodes[i]] = i
    graph = nx.relabel_nodes(graph, labels)
    
    return graph


def main():
    """Run the game"""
    random.seed(42)
    graph = build_graph()

    # Initialise players
    red = Player("red", start_node=0)
    blue = Player("blue", start_node=graph.number_of_nodes()-1)

    # Initialise flags
    red_flag = Flag("red", base_node=0)
    blue_flag = Flag("blue", base_node=graph.number_of_nodes()-1)

    # Initialise and begin the game
    game = CaptureTheFlag(graph, red, blue, red_flag, blue_flag)
    game.play()

if __name__ == "__main__":
    main()