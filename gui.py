import tkinter as tk
from tkinter import messagebox

# Base class: 
class User:  #base class User to represent shared attributees for voters and admins hence abstraction
    def __init__(self, user_id, name):
        self._user_id = user_id  #encapsulation
        self._name = name

    def get_details(self): #method to return user details thus abstraction.
        print(f"[User.get_details] Returning user info for {self._name}")
        return f"User ID: {self._user_id}, Name: {self._name}"

# Subclass: 
class Voter(User):  #inherits from User
    def __init__(self, user_id, name):
        super().__init__(user_id, name) #calls base class constructor to initialize shared attributes
        self._has_voted = False #tracks whether voter has voted.

    def vote(self, candidate, system):#method for casting vote.
        if self._has_voted: #checks if voter has already voted and prints a warning.
            print(f"[Voter.vote] {self._name} has already voted.")
        else:#if not voted, records the vote and updates the status.
            print(f"[Voter.vote] {self._name} is voting for {candidate}.")
            system.record_vote(candidate)
            self._has_voted = True

    def get_details(self): #overrides hence demonstrating polymorphism.
        print(f"[Voter.get_details] Returning voter info for {self._name}")
        status = "Voted" if self._has_voted else "Not Voted"#appends voting status to base user details.
        return super().get_details() + f", Status: {status}"

# Subclass: Admin 
class Admin(User): #inherits from user
    def __init__(self, user_id, name):
        super().__init__(user_id, name) #initializes shared attributes via base class

    def view_results(self, system):
        print(f"[Admin.view_results] {self._name} is viewing results.")
        return system.get_results() #allows admin to view the results.

    def get_details(self): #overrides to indicate admin role thus polyphorphism
        print(f"[Admin.get_details] Returning admin info for {self._name}")
        return super().get_details() + " (Admin)"

# Voting System 
class VotingSystem:
    def __init__(self, candidates): #initialize with a list of candidates
        self._candidates = candidates #stores names and initializes voter counts
        self._votes = {candidate: 0 for candidate in candidates}

    def record_vote(self, candidate): #record a vote.
        if candidate in self._votes:
            self._votes[candidate] += 1 #increments vote count
            print(f"[VotingSystem.record_vote] Vote recorded for {candidate}.")
        else: #handling invalid candidates names
            print(f"[VotingSystem.record_vote] Invalid candidate: {candidate}")

    def get_results(self): #returning voting tally
        print("[VotingSystem.get_results] Returning vote counts.")
        return self._votes

class E_VotingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Voting System")
        self.voting_system = VotingSystem(["Tarsis", "Isabelle", "George"])
        # Predefined voters and admins to separate roles
        self.voters = {
            1: Voter(1, "Jane Rice"),
            2: Voter(2, "Steve Jobs")
        }
        self.admins = {
            99: Admin(99, "Election Officer")
        }

        # Main menu
        tk.Button(root, text="Login as Voter", command=self.voter_login).pack(pady=10)
        tk.Button(root, text="Login as Admin", command=self.admin_login).pack(pady=10)

    def voter_login(self):
        login_win = tk.Toplevel(self.root)
        login_win.title("Voter Login")

        tk.Label(login_win, text="User ID:").pack(pady=5)
        id_entry = tk.Entry(login_win)
        id_entry.pack(pady=5)

        tk.Label(login_win, text="Name:").pack(pady=5)
        name_entry = tk.Entry(login_win)
        name_entry.pack(pady=5)

        def submit():
            try:
                user_id = int(id_entry.get())
                name = name_entry.get().strip()
                if not name:
                    messagebox.showerror("Error", "Name cannot be empty")
                    return
                if user_id not in self.voters:
                    messagebox.showerror("Error", "Invalid Voter ID")
                    return
                voter = self.voters[user_id]
                if voter._name != name:
                    messagebox.showerror("Error", "Name mismatch for this ID")
                    return
                login_win.destroy()
                self.voter_dashboard(voter)
            except ValueError:
                messagebox.showerror("Error", "User ID must be an integer")

        tk.Button(login_win, text="Submit", command=submit).pack(pady=10)

    def voter_dashboard(self, voter):
        if voter._has_voted:
            messagebox.showinfo("Info", "You have already voted.")
            return

        dash_win = tk.Toplevel(self.root)
        dash_win.title("Voter Dashboard")

        tk.Label(dash_win, text=f"Welcome, {voter._name}").pack(pady=10)
        tk.Label(dash_win, text="Select Candidate:").pack(pady=5)

        candidate_var = tk.StringVar(dash_win)
        if self.voting_system._candidates:
            candidate_var.set(self.voting_system._candidates[0])
        tk.OptionMenu(dash_win, candidate_var, *self.voting_system._candidates).pack(pady=5)

        def vote():
            if not self.voting_system._candidates:
                messagebox.showerror("Error", "No candidates available")
                return
            cand = candidate_var.get()
            voter.vote(cand, self.voting_system)
            dash_win.destroy()
            messagebox.showinfo("Success", "Vote cast successfully")

        tk.Button(dash_win, text="Vote", command=vote).pack(pady=10)

    def admin_login(self):
        login_win = tk.Toplevel(self.root)
        login_win.title("Admin Login")

        tk.Label(login_win, text="User ID:").pack(pady=5)
        id_entry = tk.Entry(login_win)
        id_entry.pack(pady=5)

        tk.Label(login_win, text="Name:").pack(pady=5)
        name_entry = tk.Entry(login_win)
        name_entry.pack(pady=5)

        def submit():
            try:
                user_id = int(id_entry.get())
                name = name_entry.get().strip()
                if not name:
                    messagebox.showerror("Error", "Name cannot be empty")
                    return
                if user_id not in self.admins:
                    messagebox.showerror("Error", "Invalid Admin ID")
                    return
                admin = self.admins[user_id]
                if admin._name != name:
                    messagebox.showerror("Error", "Name mismatch for this ID")
                    return
                login_win.destroy()
                self.admin_dashboard(admin)
            except ValueError:
                messagebox.showerror("Error", "User ID must be an integer")

        tk.Button(login_win, text="Submit", command=submit).pack(pady=10)

    def admin_dashboard(self, admin):
        dash_win = tk.Toplevel(self.root)
        dash_win.title("Admin Dashboard")

        tk.Label(dash_win, text=f"Welcome, Admin {admin._name}").pack(pady=10)

        # Add candidate
        tk.Label(dash_win, text="Add New Candidate:").pack(pady=5)
        cand_entry = tk.Entry(dash_win)
        cand_entry.pack(pady=5)

        def add_cand():
            new_cand = cand_entry.get().strip()
            if not new_cand:
                messagebox.showerror("Error", "Candidate name cannot be empty")
                return
            if new_cand in self.voting_system._candidates:
                messagebox.showerror("Error", "Candidate already exists")
                return
            self.voting_system._candidates.append(new_cand)
            self.voting_system._votes[new_cand] = 0
            messagebox.showinfo("Success", f"Candidate '{new_cand}' added")
            cand_entry.delete(0, tk.END)

        tk.Button(dash_win, text="Add Candidate", command=add_cand).pack(pady=10)

        # View results
        def view_results():
            results = admin.view_results(self.voting_system)
            res_str = "Vote Tally:\n\n"
            for c, v in sorted(results.items()):
                res_str += f"{c}: {v} votes\n"
            messagebox.showinfo("Election Results", res_str)

        tk.Button(dash_win, text="View Results", command=view_results).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = E_VotingApp(root)
    root.mainloop()