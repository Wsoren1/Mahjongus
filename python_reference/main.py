import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import random
import numpy as np

SUITS = ["s", "p", "m"]
HONORS = ["Ea", "No", "So", "We", "Gr", "Re", "Wh"]
PLAYER_NAMES = ["East", "South", "West", "North"]  # Player names

class MahjongGame:
    def __init__(self):
        self.drawing_order = None
        self.hands = None
        self.current_player = 0
        self.dead_wall = None
        self.discard_piles = [[] for _ in range(4)] # Initialize discard piles for each player
        self.open_melds = [[] for _ in range(4)]  # Open melds for each player
        self.dora_indicators = []  # List of Dora indicator tiles
        self.kan_count = 0
        self.kan_player = None
        self.concealed_kans = [[] for _ in range(4)] # List of concealed Kans for each player
        self.riichi_players = [False] * 4  # Track Riichi status for each player
        self.riichi_wait = [None] * 4  # Tiles each player is waiting on for Ron

    def create_tileset(self):
        """Creates a standard Riichi Mahjong tileset."""
        tiles = []
        # Basic tiles
        for suit in SUITS:
            for value in range(1, 10):
                for _ in range(4):
                    tile = f"{value}{suit}"
                    tiles.append(tile)
                if value == 5:  # Add the red 5
                    tiles.remove("5" + suit)  # Remove a regular 5
                    tiles.append(f"5{suit}*") # Add the red 5

        # Honor tiles
        for honor in HONORS:
            for _ in range(4):
                tiles.append(honor)

        return tiles

    def organize_hand(self, hand):
        """Organizes the hand for readability: suits, numbers, honors."""

        def tile_sort_key(tile):
            if tile[1] == 's':
                suit_order = 0
                value = int(tile[:-1]) if '*' not in tile else int(tile[:-2])
            elif tile[1] == 'p':
                suit_order = 1
                value = int(tile[:-1]) if '*' not in tile else int(tile[:-2])
            elif tile[1] == 'm':
                suit_order = 2
                value = int(tile[:-1]) if '*' not in tile else int(tile[:-2])
            else:  # Honor tiles
                suit_order = 3
                if tile in ["Ea", "No", "So", "We"]:
                    value = HONORS.index(tile)
                else:
                    value = HONORS.index(tile) + 10  # Place dragons after winds

            return (suit_order, value, tile)  # Include tile itself for tie-breaker (red 5s)

        return sorted(hand, key=tile_sort_key)

    def build_walls(self, tiles):
        """Shuffles and builds walls from the tileset."""
        random.shuffle(tiles)
        walls = [tiles[i:i+34] for i in range(0, len(tiles), 34)]
        walls = [np.reshape(wall, (2, 17)) for wall in walls]

        return walls

    def get_next_dora(self):
        if len(self.dead_wall[0]) > len(self.dora_indicators) + 1:
            next_dora = self.dead_wall[0][len(self.dora_indicators) + 1]
            self.dora_indicators.append(next_dora)
            print(f"New Dora indicator revealed: {next_dora}")
        else:
            print("All Dora indicators revealed from dead wall.")
            if self.kan_player != -1:  # Check for four quads draw condition
                # Implement four quads draw logic here
                pass

    def determine_dead_wall(self, walls, dealer_roll):
        """Determines the dead wall based on the dice roll."""
        wall_index = (dealer_roll - 1) % 4
        tile_index = 17 - (dealer_roll) # Count from right, both rows

        dead_wall = []

        if tile_index > 10:
            A = walls[wall_index][:, tile_index:]
            walls[wall_index] = walls[wall_index][:, :tile_index]

            B = walls[(wall_index - 1) % 4][:, :(tile_index + 7) % 17]
            walls[(wall_index - 1) % 4] = walls[(wall_index - 1) % 4][:, (tile_index + 7) % 17:]

            dead_wall = np.array([np.concatenate((A[0], B[0])), np.concatenate((A[1], B[1]))])
        else:

            dead_wall = walls[wall_index][:, tile_index:tile_index + 7]
            A = walls[wall_index][:, :tile_index]
            B = walls[wall_index][:, tile_index + 7:]

            walls[wall_index] = A
            walls[(wall_index - 1) % 4] = np.array((np.concatenate((B[0], walls[(wall_index - 1) % 4][0])), np.concatenate((B[1], walls[(wall_index - 1) % 4][1]))))

        return dead_wall, walls

    def deal_hands(self, walls):
        """Deals hands to the four players."""
        hands = [[], [], [], []]
        wall_index = 0
        tile_index = 0

        wall_index = np.argmin([len(wall[0]) for wall in walls])
        player = 0

        drawing_order = []
        for wall in walls:
            drawing_order = np.concatenate((drawing_order, np.array([row[::-1] for row in wall]).flatten()))

        for _ in range(16):
            hands[player] = np.concatenate((hands[player], drawing_order[:3]))
            player = (player + 1) % 4
            drawing_order = drawing_order[3:]

        for _ in range(4):
            hands[player] = np.concatenate((hands[player], [drawing_order[0]]))
            player = (player + 1) % 4
            drawing_order = drawing_order[1:]

        # ... Inside the deal_hands function, after populating drawing_order:
        self.drawing_order = drawing_order
        return hands

    def draw_next_tile(self):
        if len(self.drawing_order) == 0:
            return None  # No more tiles to draw
        tile = self.drawing_order[0]
        self.drawing_order = self.drawing_order[1:]
        return tile

    def discard_tile(self, player_index, tile_index):
        """Discards the tile at the given index from the player's hand."""
        discarded_tile = self.hands[player_index][tile_index]
        self.hands[player_index] = np.delete(self.hands[player_index], tile_index)
        self.discard_piles[player_index].append(discarded_tile)

    def print_discard_piles(self):
        """Prints the current state of all players' discard piles."""
        print("\nDiscard Piles:")
        for i, pile in enumerate(self.discard_piles):
            row_count = len(pile) // 6 + (1 if len(pile) % 6 else 0)
            print(f"Player {i + 1}:")
            for r in range(row_count):
                row_start = r * 6
                row_end = min(row_start + 6, len(pile))
                print(" ".join(pile[row_start:row_end]))

    def can_pon(self, player_index, discarded_tile):
        """Checks if the player can call Pon on the discarded tile."""
        hand = list(self.hands[player_index])
        count = hand.count(discarded_tile)
        return count >= 2

    def can_kan(self, player_index, discarded_tile):
        """Checks if the player can call Kan on the discarded tile."""
        hand = list(self.hands[player_index])
        count = hand.count(discarded_tile)
        return count >= 3

    def perform_kan(self, player_index, discarded_tile, discarding_player_index):
        """Executes the Kan call."""
        hand = self.hands[player_index]
        indices_to_remove = []
        count = 0
        for i, tile in enumerate(hand):
            if tile == discarded_tile and count < 3:
                indices_to_remove.append(i)
                count += 1

        for index in sorted(indices_to_remove, reverse=True):
            hand = np.delete(hand, index)

        self.hands[player_index] = hand
        self.discard_piles[discarding_player_index].pop()

        # Add to open melds
        self.open_melds[player_index].append([discarded_tile] * 4)

        # Reveal next Dora indicator
        self.get_next_dora()

        # Update Kan count and player
        self.kan_count += 1
        if self.kan_player is None:
            self.kan_player = player_index
        elif self.kan_player != player_index:
            self.kan_player = -1  # More than one player called Kan


        print(f"Player {player_index + 1} called Kan on {discarded_tile}!")

    def can_chii(self, player_index, discarded_tile):
        """Checks if the player can call Chii on the discarded tile."""
        if discarded_tile in HONORS:
            return False

        if (player_index - self.current_player) % 4 != 1:
            return False # Only the next player in turn order can call Chii

        hand = self.hands[player_index]
        tile_value = int(discarded_tile[0]) if '*' not in discarded_tile else int(discarded_tile[0])
        suit = discarded_tile[1]

        for i in range(1, 10):
            if (f"{i}{suit}" in hand and f"{i+1}{suit}" in hand and tile_value == i+2) or \
               (f"{i}{suit}" in hand and f"{i+2}{suit}" in hand and tile_value == i+1) or \
               (f"{i+1}{suit}" in hand and f"{i+2}{suit}" in hand and tile_value == i):
                return True
        return False

    def perform_chii(self, player_index, discarded_tile, discarding_player_index):
        """Executes the Chii call, prompting for the specific sequence if needed."""
        hand = self.hands[player_index]
        tile_value = int(discarded_tile[0]) if '*' not in discarded_tile else int(discarded_tile[0])
        suit = discarded_tile[1]

        possible_sequences = []
        for i in range(1, 10):
            if f"{i}{suit}" in hand and f"{i+1}{suit}" in hand and tile_value == i+2:
                possible_sequences.append((f"{i}{suit}", f"{i+1}{suit}", discarded_tile))
            if f"{i}{suit}" in hand and f"{i+2}{suit}" in hand and tile_value == i+1:
                possible_sequences.append((f"{i}{suit}", discarded_tile, f"{i+2}{suit}"))
            if f"{i+1}{suit}" in hand and f"{i+2}{suit}" in hand and tile_value == i:
                possible_sequences.append((discarded_tile, f"{i+1}{suit}", f"{i+2}{suit}"))

        if len(possible_sequences) > 1:
            print("Possible sequences:")
            for idx, seq in enumerate(possible_sequences):
                print(f"{idx + 1}: {' '.join(seq)}")
            choice = int(input("Choose a sequence (enter number): ")) - 1
            chosen_sequence = possible_sequences[choice]
        else:
            chosen_sequence = possible_sequences[0]

        for tile in chosen_sequence:
            index = np.where(hand == tile)[0]
            hand = np.delete(hand, index)

        self.hands[player_index] = hand
        self.discard_piles[discarding_player_index].pop()
        self.open_melds[player_index].append(chosen_sequence)
        # Add the Chii set to an open meld area
        print(f"Player {player_index + 1} called Chii with {' '.join(chosen_sequence)}!")

    def perform_pon(self, player_index, discarded_tile, discarding_player_index):
        """Executes the Pon call: removes tiles from hand, updates discard pile."""
        hand = self.hands[player_index]
        count = 0
        indices_to_remove = []
        for i, tile in enumerate(hand):
            if tile == discarded_tile and count < 2:
                indices_to_remove.append(i)
                count += 1

        # Remove the two tiles from the hand in reverse order to avoid index issues
        for index in sorted(indices_to_remove, reverse=True):
            hand = np.delete(hand, index)

        self.hands[player_index] = hand

        # Remove the tile from the discarding player's discard pile
        self.discard_piles[discarding_player_index].pop()

        self.open_melds[player_index].append([discarded_tile] * 3)
        print(f"Player {player_index + 1} called Pon on {discarded_tile}!")

    def perform_concealed_kan(self, tile):
        """Performs a concealed Kan, updating hand, melds, and Dora indicators."""

        hand = self.hands[self.current_player]
        for _ in range(4):  # Remove all four tiles from hand
            index = np.where(hand == tile)[0][0]  # Find the first index of the tile
            hand = np.delete(hand, index)
        self.hands[self.current_player] = hand

        # Add to concealed Kans
        self.concealed_kans[self.current_player].append([tile] * 4)

        # Reveal next Dora indicator


        print(f"Player {self.current_player + 1} called Concealed Kan on {tile}!")

    def handle_call(self, discarded_tile, discarding_player_index):
        """Handles all call opportunities (Pon, Kan, Chii) after a discard."""
        for player_index in range(4):
            if player_index != discarding_player_index:
                if self.can_kan(player_index, discarded_tile):
                    if input(f"Player {player_index + 1} (of {PLAYER_NAMES[player_index]}), call Kan on {discarded_tile}? (y/n): ").lower() == 'y':
                        self.perform_kan(player_index, discarded_tile, discarding_player_index)
                        self.current_player = player_index
                        if game.is_complete_hand(game.current_player):
                            print(f"Player {game.current_player + 1} has a complete hand!")

                        return True

                if self.can_pon(player_index, discarded_tile):
                    if input(f"Player {player_index + 1} (of {PLAYER_NAMES[player_index]}), call Pon on {discarded_tile}? (y/n): ").lower() == 'y':
                        self.perform_pon(player_index, discarded_tile, discarding_player_index)
                        self.current_player = player_index
                        if game.is_complete_hand(game.current_player):
                            print(f"Player {game.current_player + 1} has a complete hand!")

                        return True

                if self.can_chii(player_index, discarded_tile):
                    if input(f"Player {player_index + 1} (of {PLAYER_NAMES[player_index]}), call Chii on {discarded_tile}? (y/n): ").lower() == 'y':
                        self.perform_chii(player_index, discarded_tile, discarding_player_index)
                        self.current_player = player_index
                        if game.is_complete_hand(game.current_player):
                            print(f"Player {game.current_player + 1} has a complete hand!")

                        return True
        return False

    def turn_prompt(self, called=False):
        player_name = PLAYER_NAMES[self.current_player]  # Get player name
        print(f"\nCurrent Dora indicators: {' '.join(self.dora_indicators)}")
        print(f"\n{player_name}'s Turn:")
        print(f"Hand: {' '.join(self.hands[self.current_player])}")


        if self.riichi_players[self.current_player]:
            # Riichi turn: draw and check for Tsumo or Ron only
            drawn_tile = self.draw_next_tile()
            if drawn_tile:
                print(f"Drew tile: {drawn_tile}")
                self.hands[self.current_player] = np.concatenate(
                    (self.hands[self.current_player], [drawn_tile])
                )

                if self.is_complete_hand(self.current_player):
                    print(f"Player {self.current_player + 1} wins by Tsumo!")
                    return 0

                discard_index = np.where(self.hands[self.current_player] == drawn_tile)[0][0]
                self.discard_tile(self.current_player, discard_index)
                self.print_discard_piles()
                discard_tile = drawn_tile

        else:
            drawn_tile = self.draw_next_tile() if not called else 'null_tile'


            if drawn_tile:
                if not called:
                    print(f"Drew tile: {drawn_tile}")
                    self.hands[self.current_player] = np.concatenate(
                        (self.hands[self.current_player], [drawn_tile])
                    )
                    if not self.riichi_players[self.current_player]:  # Riichi players don't choose discard
                        wait_tiles = self.check_riichi_ready(self.current_player)
                        if len(wait_tiles) > 0 and input(f"Player {self.current_player + 1} (of {PLAYER_NAMES[self.current_player]}), declare Riichi? (y/n): ").lower() == 'y':
                            self.declare_riichi(self.current_player, wait_tiles)



                    if list(self.hands[self.current_player]).count(drawn_tile) == 4:
                        if input(f"Player {self.current_player + 1} (of {PLAYER_NAMES[self.current_player]}), call Concealed Kan on {drawn_tile}? (y/n): ").lower() == 'y':
                            self.perform_concealed_kan(drawn_tile)
                            self.turn_prompt(called=False) # Turn resets
                            self.get_next_dora()
                            return 1

                # Check for Tsumo (self-draw win)
                if self.is_complete_hand(self.current_player):
                    if input(f"Player {self.current_player + 1} (of {PLAYER_NAMES[self.current_player]}), call Tsumo on {drawn_tile}? (y/n): ").lower() == 'y':
                        print(f"Player {self.current_player + 1} wins by Tsumo!")
                        # Handle points calculation and end of round here (not implemented)
                        return 0

                while True:
                    discard_prompt = f" (or 'd' to discard the drawn tile '{drawn_tile}')" if not called else ""
                    discard_tile_str = input("Enter the tile to discard" + discard_prompt + ": ")
                    if (not called) and (discard_tile_str.lower() == 'd'):
                        discard_tile = drawn_tile
                        discard_index = np.where(self.hands[self.current_player] == drawn_tile)[0][0]
                        break
                    elif discard_tile_str in self.hands[self.current_player]:
                        discard_tile = discard_tile_str
                        discard_index = np.where(self.hands[self.current_player] == discard_tile)[0][0]
                        break
                    else:
                        print("Invalid tile. Please try again.")

                self.discard_tile(self.current_player, discard_index)
                self.print_discard_piles()

            else:
                print("No more tiles to draw!")
                return 0


        if self.handle_ron(discard_tile, self.current_player):
            # If there was a Ron, end the round
            return 0

        if self.handle_call(discard_tile, self.current_player): # Handle calls after discarding
            # If there was a call, skip the normal turn progression
            self.turn_prompt(called=True)
            return 1

        self.hands[self.current_player] = self.organize_hand(self.hands[self.current_player])
        self.current_player = (self.current_player + 1) % 4
        return 1

    def print_discard_piles(self):
        """Prints the current state of all players' discard piles."""

        print(f"\nCurrent Dora indicators: {' '.join(self.dora_indicators)}")

        #print("\nDiscard Piles and Open Melds:")
        for i, pile in enumerate(self.discard_piles):
            player_name = PLAYER_NAMES[i]
            print(f"{player_name}:")

            # Display open melds
            #if len(self.open_melds[i]) > 0:
            #    print("  Open Melds:", [" ".join(meld) for meld in self.open_melds[i]])

            if len(self.open_melds[i]) > 0 or len(self.concealed_kans[i]) > 0:
                print("  Melds (Open & Concealed):",
                      [" ".join(meld) for meld in self.open_melds[i]],
                      ["(Concealed) " + " ".join(meld) for meld in self.concealed_kans[i]])
        print("\nDiscard Piles:")
        for i, pile in enumerate(self.discard_piles):
            player_name = PLAYER_NAMES[i]  # Get player name
            row_count = len(pile) // 6 + (1 if len(pile) % 6 else 0)
            print(f"{player_name}:")
            for r in range(row_count):
                row_start = r * 6
                row_end = min(row_start + 6, len(pile))
                print(" ".join(pile[row_start:row_end]))

    def start_game(self):
        tiles = self.create_tileset()
        walls = self.build_walls(tiles)
        dealer_roll = random.randint(2, 12)
        dead_wall, walls = self.determine_dead_wall(walls, dealer_roll)
        self.dead_wall = dead_wall

        self.hands = self.deal_hands(walls)

        # Organize hands after dealing
        for i in range(len(self.hands)):
            self.hands[i] = self.organize_hand(self.hands[i])

        self.dora_indicators.append(self.dead_wall[0][1])  # First Dora indicator

        print(f"Initial Dora indicator: {self.dora_indicators[-1]}")
        for i, hand in enumerate(self.hands):
            print(f"Player {i + 1} Hand: {' '.join(hand)}")

    def handle_ron(self, discarded_tile, discarding_player_index):
        """Handles Ron opportunities for all players after a discard."""
        for player_index in range(4):
            if player_index != discarding_player_index:

                if self.riichi_players[player_index] and discarded_tile in self.riichi_wait[player_index]:
                    # Riichi player can only Ron on their wait tile
                    print(f"Player {player_index + 1} wins by Ron!")
                    return True
                elif not self.riichi_players[player_index]:
                    temp_hand = np.concatenate((self.hands[player_index], [discarded_tile]))
                    if self.is_complete_hand_temp(temp_hand):  # Check if hand is complete with discarded tile
                        if input(f"Player {player_index + 1} (of {PLAYER_NAMES[player_index]}), call Ron on {discarded_tile}? (y/n): ").lower() == 'y':
                            print(f"Player {player_index + 1} wins by Ron!")
                            # Handle points calculation and end of round here (not implemented)
                            return True  # End the round
        return False

    def is_complete_hand(self, player_index):
        """
        Checks if the player's hand (including open melds) forms a complete hand.
        A complete hand consists of 4 sets (triplets or sequences) and a pair, all in the same suit.
        """

        tiles = list(self.hands[player_index])
        melds = self.open_melds[player_index] + self.concealed_kans[player_index]

        blocks = []
        unmatched = list(tiles)  # Start with all tiles as unmatched

        # Helper to remove tiles from unmatched list once in a block
        def mark_as_matched(tile_list):
            for tile in tile_list:
                if tile in unmatched:
                    unmatched.remove(tile)

        # Identify triplets
        for tile in set(tiles):  # Check unique tiles
            count = tiles.count(tile)
            if count >= 3:
                blocks.append((tile, tile, tile))
                mark_as_matched([tile] * 3)

        # Identify sequences (numerical tiles only)
        suits = ['s', 'p', 'm']
        for suit in suits:
            suit_tiles = sorted([int(tile[:-1]) for tile in tiles if tile.endswith(suit)])
            i = 0
            while i < len(suit_tiles) - 2:
                if suit_tiles[i+1] == suit_tiles[i] + 1 and suit_tiles[i+2] == suit_tiles[i] + 2:
                    block = [f"{num}{suit}" for num in suit_tiles[i:i+3]]
                    blocks.append(tuple(block))
                    mark_as_matched(block)
                    i += 3  # Skip ahead as we found a sequence
                else:
                    i += 1

        # Identify pairs
        for tile in set(unmatched):  # Check remaining unmatched tiles
            count = tiles.count(tile)
            if count >= 2:
                blocks.append((tile, tile))
                mark_as_matched([tile] * 2)

        return (len(blocks) + len(melds) == 5) and (len(unmatched) == 0)

    def is_complete_hand_temp(self, hand):
        """
        Checks if the provided temporary hand (including open melds) forms a complete hand.
        This is used to check Ron possibilities without modifying the actual hand.
        """
        tiles = list(hand)
        melds = []
        for i in range(4):
            if i == self.current_player:  # Use melds from current player only for win check
                melds.extend(self.open_melds[i] + self.concealed_kans[i])

        blocks = []
        unmatched = list(tiles)  # Start with all tiles as unmatched

        # (rest of the is_complete_hand logic adapted for a temporary hand - as previously provided)
        # Helper to remove tiles from unmatched list once in a block
        def mark_as_matched(tile_list):
            for tile in tile_list:
                if tile in unmatched:
                    unmatched.remove(tile)

        # Identify triplets
        for tile in set(tiles):  # Check unique tiles
            count = tiles.count(tile)
            if count >= 3:
                blocks.append((tile, tile, tile))
                mark_as_matched([tile] * 3)

        # Identify sequences (numerical tiles only)
        suits = ['s', 'p', 'm']
        for suit in suits:
            suit_tiles = sorted([int(tile[:-1]) if '*' not in tile else int(tile[:-2]) for tile in tiles if tile.endswith(suit)])
            i = 0
            while i < len(suit_tiles) - 2:
                if suit_tiles[i+1] == suit_tiles[i] + 1 and suit_tiles[i+2] == suit_tiles[i] + 2:
                    block = [f"{num}{suit}" for num in suit_tiles[i:i+3]]
                    blocks.append(tuple(block))
                    mark_as_matched(block)
                    i += 3  # Skip ahead as we found a sequence
                else:
                    i += 1

        # Identify pairs
        for tile in set(unmatched):  # Check remaining unmatched tiles
            count = tiles.count(tile)
            if count >= 2:
                blocks.append((tile, tile))
                mark_as_matched([tile] * 2)

        return (len(blocks) + len(melds) == 5) and (len(unmatched) == 0)

    def check_riichi_ready(self, player_index):
        """Checks if a player is one tile away from a winning hand."""
        hand = self.hands[player_index]
        unique_tiles = set(hand)
        wait_tiles = []
        for tile in unique_tiles:
            temp_hand = list(hand)  # Create a copy to test
            temp_hand.remove(tile)
            if self.is_complete_hand_temp(temp_hand):
                wait_tiles.append(tile)  # Return the tile that would complete the hand
        return wait_tiles

    def declare_riichi(self, player_index, wait_tiles):
        """Declares Riichi for the given player."""
        self.riichi_players[player_index] = True
        self.riichi_wait[player_index] = wait_tiles
        print(f"Player {player_index + 1} declares Riichi!")

random.seed(29)

# 23 good concealed kan test

# Example usage
game = MahjongGame()
game.start_game()
game.hands[3] = ['1s', '2s', '3s', '5s', '5s', '5s', '6p', '6p', 'Re', 'Re', 'Re', 'So', 'So']
for player in range(4):
    for tile in game.drawing_order:
        if game.can_kan(player, tile):
            print(f"{player}: kan wait with {tile}")

# Simulate turns
while game.turn_prompt():
    if game.is_complete_hand(game.current_player):
        print(f"Player {game.current_player + 1} has a complete hand!")
