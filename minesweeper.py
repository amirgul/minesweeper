import itertools
import random
import sys

class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False) # FALSE = SAFE CELL
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines: # NOT IT IS ADDING 8 MINES
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j)) # A cell is a TUPLE (i,j) type
                self.board[i][j] = True # TRUE = MINE CELL

        # At first, player has found no mines
        self.mines_found = set()

        # FOR TESTING PURPOSES: Double check the answers found by the AI
        # f = open("answerMines.txt", "w")
        # f.write(f"MINES{self.mines}")
        # f.close()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count
        #print(f"Sentence.init: {{ {self.cells} }}, count {self.count}")

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if len(self.cells)==self.count:
            #print(f"Sentence.known_mines(): deducing that {self.cells} with count {self.count} are MINES")
            return self.cells
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if self.count==0:
            #print(f"Sentence.known_safes(): deducing that {self.cells} with count {self.count} are SAFES")
            return self.cells
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.count = self.count-1
            self.cells.remove(cell)

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)

class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []


    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)


    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of `cell` and `count`

            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        self.moves_made.add(cell) # Register new move
        self.mark_safe(cell)    # Mark current cell as safe

        # Find all neighboors of 'cell'
        cell_neighbors = set()
        cell_count = count
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                # Ignore the cell itself
                if (i, j) == cell:
                    continue
                # Add This mine if in bounds and is neighboor of cell
                if 0 <= i < self.height and 0 <= j < self.width:
                    if (not (i,j) in self.mines) and (not (i,j) in self.moves_made):
                        cell_neighbors.add((i,j))
                    if (i,j) in self.mines:
                        cell_count = cell_count-1

        # Make a Sentence with all neighboors of 'cell', using 'count'
        sentence_i = Sentence(cell_neighbors, cell_count) #

        # Add the new sentence to the knowledge base
        self.knowledge.append(sentence_i)

        # Update the knowledge base to mark all newlyfound safe and mine cells
        # Removes empty sentences and sentences that are known to be all mines or all safes
        while(self.remove_empties_and_safes_and_Mines() or self.update_mines_and_safes_in_KB() ):
            pass
        # This block is for inferring new sentences
        # Copmrares every sentence in Knowledge against other sentences in Knowledge
        i_max = len(self.knowledge)
        while i < i_max:
            j_max = len(self.knowledge)
            while j < j_max:
                # Same Sentence in i and j: skip
                if (i == j):
                    j += 1
                    continue
                # Different Sentences are Equivalent . Remove One of them (j)
                if(self.knowledge[i] == self.knowledge[j]):
                    self.knowledge.remove(self.knowledge[j])
                    i_max -= 1
                    j_max -= 1
                    if j<i :
                        i -= 1
                    continue
                # Current Sentence_j is a proper subset of Sentence_i: Sentence_i-Sentence_j = New_Sentence, with new count = i_count-j_count
                if self.knowledge[j].cells < self.knowledge[i].cells:
                    new_set = self.knowledge[i].cells.difference(self.knowledge[j].cells)
                    tci = self.knowledge[i].count # Substracting self.knowledge[i].count-self.knowledge[j].count modifies count of sentence [i]
                    tcj = self.knowledge[j].count
                    new_count = tci - tcj
                    new_sentence = Sentence(new_set, new_count)
                    self.knowledge.append(new_sentence)
                j += 1
            i += 1

        # Update the knowledge base to mark all newlyfound safe and mine cells
        # Removes empty sentences and sentences that are known to be all mines or all safes
        while(self.remove_empties_and_safes_and_Mines() or self.update_mines_and_safes_in_KB() ):
            pass
        self.print_aiStatus("ai.Status")

    def update_mines_and_safes_in_KB(self):
        anyModifications = False
        # Update all Sentences in KB with cells known to be mines
        for safe_cell_i in self.safes.copy():
            for sentence in self.knowledge.copy():
                if(safe_cell_i in sentence.cells):
                    anyModifications = True
                sentence.mark_safe(safe_cell_i)
        # Update all Sentences in KB with cells known to be safes
        for mine_cell_i in self.mines.copy():
            for sentence in self.knowledge.copy():
                if(mine_cell_i in sentence.cells):
                    anyModifications = True
                sentence.mark_safe(mine_cell_i)
        return anyModifications

    def remove_empties_and_safes_and_Mines(self):
        anyRemovals = False
        for i_sentence in self.knowledge.copy():
            # Remove empty Sentences from Knowledge
            if len(i_sentence.cells)==0:
                anyRemovals = True
                self.knowledge.remove(i_sentence)
            # Remove Sentences from kB whose cells are all mines
            elif i_sentence.known_mines():
                anyRemovals = True
                for cofirmed_mine in i_sentence.known_mines().copy():
                    self.mark_mine(cofirmed_mine)
                self.knowledge.remove(i_sentence)
            # Remove Sentences from KB whose cells are all safes
            elif i_sentence.known_safes():
                anyRemovals = True
                for confirmed_safe in i_sentence.known_safes().copy():
                    self.mark_safe(confirmed_safe)
                self.knowledge.remove(i_sentence)
        return anyRemovals

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        for safe_move in self.safes:
            if (safe_move not in self.moves_made) and (safe_move not in self.mines):
                return safe_move
        return None #"None"

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """

        for i in range(self.height):
            for j in range(self.width):
                random_cell = (i,j)
                if (random_cell not in self.moves_made) and (random_cell not in self.mines):
                    return random_cell
        return None

    def print_aiStatus(self, message):
        print(f"{message.upper()}\n\tai.moves_made: {self.moves_made}\n\tai.mines: {self.mines}, \n\tai.safes: {self.safes}, \n\tai.knowledge: ")
        for s in self.knowledge:
            print(f"\t\t{s.cells},= {s.count}")
