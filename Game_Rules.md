# Capture the Flag Graph Implementation Rules

## Game Overview
An implementation of Capture the Flag - a popular game requiring teams to caputre their opponent's flag and return it to their base before the other team(s) - as a two-player, turn based, strategic game played on a graph $G = (V,E)$, where:
- Vertices $V$ represent positions on a map,
- and Edges $E$ represent possible moves between vertices.

Each user controls a team containing one or more 'players' that move along the edges of the graph.
Each team has a 'flag' placed at a designated node on the graph, known as the 'base node'.
The objective is to manouvre the players to capture the opponents flag and return it to your own base node, whilst defending your own flag.

## Definitions

### Teams
- Two teams: Red and Blue
- Each team has:
    - A base node $b_R/b_B \in V$,
    - A flag,
    - One or more players.

### Flags
- Each team's flag begins in their base node.
- A flag can be captured, carried and returned.
- A team can only win by carrying their opponent's flag to their base node.

### Graph
- The game will be played on a game consisting of nodes, determining where a player can be and edges, determining where a player can move to.
- Different graph types (path, cycle, random, bipartite, etc.) determine the structural and strategical difficulty.

## Gameplay

### Turns
The game will be played using alternating turns, where one player (red) will go first.
In each turn, there will be several steps to follow:
1. The team will move one player to an adjacent node.
2. Flag capture/collision rules will be applied.
3. Winning conditions will be checked.
4. Turn passes to the other player.

#### Movement
- Players can move across one edge per turn.
- A move is only valid if the target node is adjacent to the current node.
- Players can move onto nodes occupied by other players (including opponents) and nodes occupied by flags.

#### Flag capture/collision rules

|-----------------------------------------------------------|-------------------------------------------------------------------------------------------|
| A player enters a node containing the opponent’s flag     | The player 'captures' the flag and begins carrying it, if the flag is not held already.   |
| A player enters a node containing their own flag          | Nothing happens.                                                                          |
| A player carrying a flag moves onto their own base node   | The player's team wins the game.                                                          |
| A player carrying a flag is intercepted by the opponent   | The flag, held by the player whose turn it is not, is dropped and returned to its base.   |

#### Tagging
If two players occupy the same node at the same time, a tag occurs.
- If neither player is carring a flag, nothing happens.
- If the player of the team whose turn it is carries a flag, the player will keep the flag.
- If the player of the team whose turn it is not carries a flag, that flag will be dropped and returned to its base.

#### Winning conditions
A team wins the game if:
- One of its players is carrying the opponent's flag, and
- They reach their own base node while still carrying it.