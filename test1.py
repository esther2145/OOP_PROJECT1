import tkinter as tk
from tkinter import messagebox
from abc import ABC, abstractmethod

# --- 1. ABSTRACTION & INHERITANCE (OOP CORE) ---

class Person(ABC):
    """Abstract Base Class for all people in the system (Voters and Candidates).
    Demonstrates ABSTRACTION and provides a base for INHERITANCE."""
    
    def __init__(self, name, unique_id):
        # Protected attributes for encapsulation within the Person and inherited classes
        self._name = name 
        self._id = unique_id

    @property
    def name(self):
        """Getter for the name."""
        return self._name
    
    @abstractmethod
    def display_info(self):
        """Abstract method to ensure subclasses implement their own info display."""
        pass


class Voter(Person):
    """Represents a voter. Inherits from Person."""
    # Demonstrates ENCAPSULATION for the voting status
    
    def __init__(self, name, unique_id):
        super().__init__(name, unique_id)
        self.__has_voted = False # Private attribute
    
    @property
    def has_voted(self):
        """Getter for the private voting status."""
        return self.__has_voted

    def mark_voted(self):
        """Method to change the voting status, controlling access to the private state."""
        if not self.__has_voted:
            self.__has_voted = True
            return True
        return False
        
    def display_info(self):
        """Polymorphic implementation of the abstract method."""
        status = "Voted" if self.__has_voted else "Registered"
        return f"Voter: {self._name} (ID: {self._id}) - Status: {status}"


class Candidate(Person):
    """Represents a candidate. Inherits from Person."""
    # Demonstrates ENCAPSULATION for the vote count

    def __init__(self, name, unique_id, party="Independent"):
        super().__init__(name, unique_id)
        self.__vote_count = 0 # Private attribute
        self._party = party # Protected attribute
        
    @property
    def vote_count(self):
        """Getter for the private vote count."""
        return self.__vote_count

    def add_vote(self):
        """Method to increment the vote count, controlling access to the private state."""
        self.__vote_count += 1
        
    def display_info(self):
        """Polymorphic implementation of the abstract method."""
        return f"Candidate: {self._name} ({self._party}) - Votes: {self.__vote_count}"


# --- 2. CORE LOGIC (ELECTION MANAGEMENT) ---

class Election:
    """Manages the entire election process: registration, voting, and results."""
    
    def __init__(self, candidates_data):
        self.voters = {}      # {id: Voter_object}
        self.candidates = {}  # {name: Candidate_object}
        self._is_active = True # Encapsulated state
        
        # Initialize candidates
        for name, id_val in candidates_data.items():
            self.candidates[name] = Candidate(name, id_val)

    @property
    def is_active(self):
        return self._is_active

    def register_voter(self, name, id_val):
        """Registers a new voter."""
        if not self._is_active:
             return "Election is closed."
        if id_val in self.voters:
            return f"Voter with ID {id_val} already registered."
            
        new_voter = Voter(name, id_val)
        self.voters[id_val] = new_voter
        return f"SUCCESS: Voter '{name}' registered with ID: {id_val}"
        
    def cast_vote(self, voter_id, candidate_name):
        """Records a vote."""
        if not self._is_active:
             return "Election is closed."
             
        voter = self.voters.get(voter_id)
        candidate = self.candidates.get(candidate_name)
        
        if not voter:
            return f"ERROR: Voter ID {voter_id} not found."
        if not candidate:
            return f"ERROR: Candidate '{candidate_name}' not found."
        
        if voter.mark_voted(): # Uses encapsulated method on Voter object
            candidate.add_vote() # Uses encapsulated method on Candidate object
            return f"SUCCESS: Vote cast for {candidate_name} by Voter ID {voter_id}."
        else:
            return f"ERROR: Voter ID {voter_id} has already voted."

    def get_results(self):
        """Returns the final vote count for all candidates."""
        results = {c.name: c.vote_count for c in self.candidates.values()}
        return results

# --- 3. GUI IMPLEMENTATION (TKINTER) ---

class E_Voting_GUI:
    """Basic functional GUI using Tkinter for user interaction."""

    def __init__(self, master, election_system):
        self.master = master
        self.master.title("E-Voting System v1.0")
        self.election = election_system
        
        # Set up the main frames
        self.master.config(padx=20, pady=20)
        
        # Candidate List
        tk.Label(master, text="Candidates", font=('Arial', 12, 'bold')).grid(row=0, column=0, pady=5, sticky='w')
        self.candidate_label = tk.Label(master, text="\n".join(self.election.candidates.keys()), justify=tk.LEFT)
        self.candidate_label.grid(row=1, column=0, padx=10, sticky='nw')

        # Frame for controls (Registration and Voting)
        control_frame = tk.Frame(master)
        control_frame.grid(row=0, column=1, rowspan=3, padx=20, pady=5, sticky='n')
        
        # --- Registration Section ---
        tk.Label(control_frame, text="1. Voter Registration", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=5)
        
        tk.Label(control_frame, text="Name:").grid(row=1, column=0, sticky='e')
        self.reg_name_entry = tk.Entry(control_frame)
        self.reg_name_entry.grid(row=1, column=1)
        
        tk.Label(control_frame, text="ID:").grid(row=2, column=0, sticky='e')
        self.reg_id_entry = tk.Entry(control_frame)
        self.reg_id_entry.grid(row=2, column=1)
        
        tk.Button(control_frame, text="Register", command=self.register_voter_action).grid(row=3, column=0, columnspan=2, pady=5)
        
        tk.Frame(control_frame, height=1, bg='gray').grid(row=4, column=0, columnspan=2, sticky='ew', pady=10) # Separator

        # --- Voting Section ---
        tk.Label(control_frame, text="2. Cast Vote", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=2, pady=5)
        
        tk.Label(control_frame, text="Voter ID:").grid(row=6, column=0, sticky='e')
        self.vote_id_entry = tk.Entry(control_frame)
        self.vote_id_entry.grid(row=6, column=1)
        
        tk.Label(control_frame, text="Candidate Name:").grid(row=7, column=0, sticky='e')
        self.candidate_var = tk.StringVar(control_frame)
        self.candidate_var.set(next(iter(self.election.candidates.keys()), "Select")) # Default value
        self.candidate_menu = tk.OptionMenu(control_frame, self.candidate_var, *self.election.candidates.keys())
        self.candidate_menu.grid(row=7, column=1)
        
        tk.Button(control_frame, text="VOTE!", command=self.cast_vote_action, fg='blue').grid(row=8, column=0, columnspan=2, pady=10)

        # --- Results Button ---
        tk.Button(control_frame, text="3. Show Results", command=self.show_results_action, bg='yellow').grid(row=9, column=0, columnspan=2, pady=(20, 5))


    def register_voter_action(self):
        """Action handler for voter registration."""
        name = self.reg_name_entry.get().strip()
        id_val = self.reg_id_entry.get().strip()
        
        if not name or not id_val:
            messagebox.showerror("Input Error", "Name and ID cannot be empty.")
            return

        # Core logic call
        result_message = self.election.register_voter(name, id_val)
        
        # Display feedback (meaningful interaction)
        if result_message.startswith("SUCCESS"):
            messagebox.showinfo("Registration Status", result_message)
            self.reg_name_entry.delete(0, tk.END)
            self.reg_id_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Registration Status", result_message)

    def cast_vote_action(self):
        """Action handler for casting a vote."""
        voter_id = self.vote_id_entry.get().strip()
        candidate_name = self.candidate_var.get()
        
        if not voter_id:
            messagebox.showerror("Input Error", "Voter ID cannot be empty.")
            return
        
        # Core logic call
        result_message = self.election.cast_vote(voter_id, candidate_name)

        # Display feedback (meaningful interaction)
        if result_message.startswith("SUCCESS"):
            messagebox.showinfo("Voting Status", result_message)
            self.vote_id_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Voting Status", result_message)

    def show_results_action(self):
        """Action handler to display the final results."""
        results = self.election.get_results()
        
        results_text = "--- ELECTION RESULTS ---\n"
        # Polymorphic display of results
        for name, count in results.items():
            results_text += f"{name}: {count} votes\n"
        
        # Display results (meaningful interaction)
        messagebox.showinfo("Election Results", results_text)
        
        # Optional: You could update a label in the main window instead of a messagebox


# --- 4. SYSTEM INITIALIZATION ---

if __name__ == "__main__":
    # Define initial candidates: {Name: Unique_ID}
    INITIAL_CANDIDATES = {
        "Alice Smith": "C101",
        "Bob Johnson": "C102",
        "Charlie Lee": "C103"
    }

    # Initialize the core election system
    election_system = Election(INITIAL_CANDIDATES)

    # Initialize the GUI
    root = tk.Tk()
    app = E_Voting_GUI(root, election_system)
    
    # Start the Tkinter event loop
    root.mainloop()