"""
E-Voting System (single-file)
Features:
- User registration and login (Voter, Admin)
- Admin can add/remove candidates and start/end election
- Voters can cast one vote each (vote recorded locally)
- Results view (live counts)
- Saves data to 'election_data.json'

Design principles showcased:
- Encapsulation: class internals prefixed with _ and accessed via methods
- Abstraction: Election handles persistence and ballot rules
- Inheritance: Admin and Voter inherit from abstract User
- Polymorphism: Users implement interact(); Voter.vote() vs Admin.manage()

How to run:
- Requires Python 3 (no external libraries). Run: python e_voting_system.py

Note: This is an educational demo; it is NOT production-ready nor secure for real elections.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from abc import ABC, abstractmethod
import json
import hashlib
import os
from typing import Dict, List

DATA_FILE = 'election_data.json'

# -------------------- Data Models (OOP) --------------------
class User(ABC):
    """Abstract base class for any system user."""
    def __init__(self, username: str, password: str):
        self._username = username
        # store password as hashed value (simple hashing for demo)
        self._password_hash = self._hash_password(password)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def check_password(self, password: str) -> bool:
        """Check a plaintext password against stored hash."""
        return self._hash_password(password) == self._password_hash

    @property
    def username(self) -> str:
        return self._username

    @abstractmethod
    def interact(self):
        """Abstract interaction method implemented by subclasses (polymorphism)."""
        pass


class Voter(User):
    """A voter in the system. Can cast a vote once when election is active."""
    def __init__(self, username: str, password: str):
        super().__init__(username, password)
        self._has_voted = False  # encapsulated voting flag

    @property
    def has_voted(self) -> bool:
        return self._has_voted

    def mark_voted(self):
        self._has_voted = True

    def interact(self):
        return f"Voter {self._username} can cast a vote."


class Admin(User):
    """Administrator with extra privileges like candidate management."""
    def __init__(self, username: str, password: str):
        super().__init__(username, password)

    def interact(self):
        return f"Administrator {self._username} can manage the election."


class Candidate:
    """Simple candidate model."""
    def __init__(self, name: str, manifesto: str = ''):
        self._name = name
        self._manifesto = manifesto
        self._votes = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def manifesto(self) -> str:
        return self._manifesto

    @property
    def votes(self) -> int:
        return self._votes

    def receive_vote(self):
        self._votes += 1

    def to_dict(self) -> dict:
        return {'name': self._name, 'manifesto': self._manifesto, 'votes': self._votes}

    @staticmethod
    def from_dict(d: dict):
        c = Candidate(d['name'], d.get('manifesto', ''))
        c._votes = d.get('votes', 0)
        return c


# -------------------- Election Manager (Abstraction + Encapsulation) --------------------
class Election:
    """Manages the election lifecycle, candidates, voters and persistence."""
    def __init__(self):
        self._candidates: Dict[str, Candidate] = {}
        self._voters: Dict[str, Voter] = {}
        self._admins: Dict[str, Admin] = {}
        self._active = False
        # Load existing data if present
        self.load()

    # Candidate operations
    def add_candidate(self, name: str, manifesto: str = '') -> bool:
        if name in self._candidates:
            return False
        self._candidates[name] = Candidate(name, manifesto)
        self.save()
        return True

    def remove_candidate(self, name: str) -> bool:
        if name not in self._candidates:
            return False
        del self._candidates[name]
        self.save()
        return True

    def get_candidates(self) -> List[Candidate]:
        return list(self._candidates.values())

    # User operations
    def register_voter(self, username: str, password: str) -> bool:
        if username in self._voters or username in self._admins:
            return False
        self._voters[username] = Voter(username, password)
        self.save()
        return True

    def register_admin(self, username: str, password: str) -> bool:
        if username in self._admins or username in self._voters:
            return False
        self._admins[username] = Admin(username, password)
        self.save()
        return True

    def authenticate_user(self, username: str, password: str):
        if username in self._admins and self._admins[username].check_password(password):
            return self._admins[username]
        if username in self._voters and self._voters[username].check_password(password):
            return self._voters[username]
        return None

    # Election control
    def start_election(self) -> bool:
        if self._active:
            return False
        if len(self._candidates) < 1:
            return False
        self._active = True
        self.save()
        return True

    def end_election(self) -> bool:
        if not self._active:
            return False
        self._active = False
        self.save()
        return True

    def is_active(self) -> bool:
        return self._active

    # Voting
    def cast_vote(self, voter: Voter, candidate_name: str) -> bool:
        if not self._active:
            return False
        if voter.username not in self._voters:
            return False
        if voter.has_voted:
            return False
        if candidate_name not in self._candidates:
            return False
        self._candidates[candidate_name].receive_vote()
        voter.mark_voted()
        self.save()
        return True

    # Results
    def get_results(self) -> Dict[str, int]:
        return {name: c.votes for name, c in self._candidates.items()}

    # Persistence (encapsulated)
    def save(self):
        data = {
            'active': self._active,
            'candidates': {n: c.to_dict() for n, c in self._candidates.items()},
            'voters': {u: {'has_voted': v.has_voted, 'pw_hash': v._password_hash} for u, v in self._voters.items()},
            'admins': {u: {'pw_hash': a._password_hash} for u, a in self._admins.items()}
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(DATA_FILE):
            # seed default admin and candidates for demo/story
            self._admins = {'admin': Admin('admin', 'admin123')}
            self._candidates = {
                'Aisha N.': Candidate('Aisha N.', 'Education for all'),
                'Ben K.': Candidate('Ben K.', 'Healthcare improvements'),
                'Clara M.': Candidate('Clara M.', 'Jobs and infrastructure')
            }
            self._voters = {}
            self._active = False
            self.save()
            return
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._active = data.get('active', False)
        self._candidates = {n: Candidate.from_dict(d) for n, d in data.get('candidates', {}).items()}
        self._voters = {}
        for u, ud in data.get('voters', {}).items():
            # recreate voter but preserve password hash and voted flag
            v = Voter(u, 'temppass')
            v._password_hash = ud.get('pw_hash', v._password_hash)
            if ud.get('has_voted', False):
                v.mark_voted()
            self._voters[u] = v
        self._admins = {}
        for u, ad in data.get('admins', {}).items():
            a = Admin(u, 'tempadmin')
            a._password_hash = ad.get('pw_hash', a._password_hash)
            self._admins[u] = a


# -------------------- GUI (Tkinter) --------------------
class EVotingApp:
    """Tkinter GUI application that ties the models together."""
    def __init__(self, root: tk.Tk, election: Election):
        self.root = root
        self.root.title('Simple E-Voting System')
        self._election = election
        self._current_user = None  # type: User | None

        # Setup the main frames
        self._frames = {}
        for F in (LoginFrame, RegisterFrame, VoterFrame, AdminFrame, ResultsFrame):
            frame = F(parent=self.root, controller=self)
            self._frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame('LoginFrame')

    def show_frame(self, name: str):
        frame = self._frames[name]
        frame.event_generate('<<ShowFrame>>')
        frame.tkraise()

    def login(self, username: str, password: str):
        user = self._election.authenticate_user(username, password)
        if not user:
            messagebox.showerror('Login Failed', 'Invalid credentials')
            return False
        self._current_user = user
        if isinstance(user, Admin):
            self.show_frame('AdminFrame')
        else:
            self.show_frame('VoterFrame')
        return True

    def logout(self):
        self._current_user = None
        self.show_frame('LoginFrame')

    def register_voter(self, username: str, password: str):
        ok = self._election.register_voter(username, password)
        if ok:
            messagebox.showinfo('Registered', 'Voter registered successfully. Please login.')
            self.show_frame('LoginFrame')
        else:
            messagebox.showerror('Registration Failed', 'Username already exists')

    def register_admin(self, username: str, password: str):
        ok = self._election.register_admin(username, password)
        if ok:
            messagebox.showinfo('Registered', 'Admin registered successfully.')
        else:
            messagebox.showerror('Registration Failed', 'Username already exists')

    def cast_vote(self, candidate_name: str):
        if not isinstance(self._current_user, Voter):
            messagebox.showerror('Unauthorized', 'Only voters can cast votes')
            return
        voter = self._current_user
        ok = self._election.cast_vote(voter, candidate_name)
        if ok:
            messagebox.showinfo('Vote Recorded', f'Your vote for {candidate_name} has been recorded.')
            self.show_frame('LoginFrame')
        else:
            messagebox.showerror('Vote Failed', 'Unable to cast vote. Either election inactive or you already voted')

    def add_candidate(self, name: str, manifesto: str = ''):
        ok = self._election.add_candidate(name, manifesto)
        if ok:
            messagebox.showinfo('Candidate Added', f'{name} added.')
        else:
            messagebox.showerror('Add Failed', 'Candidate may already exist')

    def remove_candidate(self, name: str):
        ok = self._election.remove_candidate(name)
        if ok:
            messagebox.showinfo('Candidate Removed', f'{name} removed.')
        else:
            messagebox.showerror('Remove Failed', 'Candidate not found')

    def start_election(self):
        ok = self._election.start_election()
        if ok:
            messagebox.showinfo('Election Started', 'Election is now active. Voters can cast votes.')
        else:
            messagebox.showerror('Start Failed', 'Election could not be started (maybe already active or no candidates)')

    def end_election(self):
        ok = self._election.end_election()
        if ok:
            messagebox.showinfo('Election Ended', 'Election stopped. Results frozen.')
        else:
            messagebox.showerror('End Failed', 'Election is not active')

    def view_results(self):
        self.show_frame('ResultsFrame')


# -------------------- Frames --------------------
class BaseFrame(tk.Frame):
    """Common utilities for frames."""
    def __init__(self, parent, controller: EVotingApp):
        super().__init__(parent)
        self.controller = controller


class LoginFrame(BaseFrame):
    def __init__(self, parent, controller: EVotingApp):
        super().__init__(parent, controller)
        tk.Label(self, text='Welcome to the E-Voting Demo', font=('Arial', 16)).pack(pady=10)
        tk.Label(self, text='Username').pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()
        tk.Label(self, text='Password').pack()
        self.password_entry = tk.Entry(self, show='*')
        self.password_entry.pack()

        tk.Button(self, text='Login', command=self._do_login).pack(pady=5)
        tk.Button(self, text='Register (Voter)', command=lambda: controller.show_frame('RegisterFrame')).pack()
        tk.Button(self, text='Exit', command=controller.root.quit).pack(pady=10)

        self.bind('<<ShowFrame>>', self.on_show)

    def on_show(self, event):
        # clear fields when shown
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def _do_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        if not u or not p:
            messagebox.showerror('Input Error', 'Enter username and password')
            return
        self.controller.login(u, p)


class RegisterFrame(BaseFrame):
    def __init__(self, parent, controller: EVotingApp):
        super().__init__(parent, controller)
        tk.Label(self, text='Register as Voter', font=('Arial', 14)).pack(pady=8)
        tk.Label(self, text='Username').pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()
        tk.Label(self, text='Password').pack()
        self.password_entry = tk.Entry(self, show='*')
        self.password_entry.pack()

        tk.Button(self, text='Register', command=self._register).pack(pady=5)
        tk.Button(self, text='Back to Login', command=lambda: controller.show_frame('LoginFrame')).pack()

        # small admin registration link (for demo purposes)
        tk.Button(self, text='Create Admin (advanced)', command=self._create_admin).pack(pady=3)

    def _register(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        if not u or not p:
            messagebox.showerror('Input Error', 'Enter username and password')
            return
        self.controller.register_voter(u, p)

    def _create_admin(self):
        if not messagebox.askyesno('Confirm', 'Creating an admin gives elevated powers. Continue?'):
            return
        u = simpledialog.askstring('Admin username', 'Enter admin username:')
        p = simpledialog.askstring('Admin password', 'Enter admin password:', show='*')
        if not u or not p:
            messagebox.showerror('Input Error', 'Admin username/password required')
            return
        self.controller.register_admin(u, p)


class VoterFrame(BaseFrame):
    """Frame where voters can select a candidate and cast a vote."""
    def __init__(self, parent, controller: EVotingApp):
        super().__init__(parent, controller)
        tk.Label(self, text='Voter Panel', font=('Arial', 14)).pack(pady=8)
        tk.Button(self, text='Logout', command=controller.logout).pack(anchor='ne')
        self.info_label = tk.Label(self, text='')
        self.info_label.pack()
        self.candidates_box = tk.Listbox(self, height=8, width=40)
        self.candidates_box.pack(pady=6)
        tk.Button(self, text='Cast Vote', command=self._cast_vote).pack()
        tk.Button(self, text='View Results', command=controller.view_results).pack(pady=4)

        self.bind('<<ShowFrame>>', self.on_show)

    def on_show(self, event):
        user = self.controller._current_user
        if not isinstance(user, Voter):
            return
        self.info_label.config(text=f'Logged in as {user.username} | Voted: {user.has_voted}')
        self.candidates_box.delete(0, tk.END)
        for c in self.controller._election.get_candidates():
            self.candidates_box.insert(tk.END, f"{c.name} — {c.manifesto}")

    def _cast_vote(self):
        sel = self.candidates_box.curselection()
        if not sel:
            messagebox.showerror('No Selection', 'Choose a candidate first')
            return
        index = sel[0]
        candidate = self.controller._election.get_candidates()[index]
        # confirm
        if not messagebox.askyesno('Confirm Vote', f'Confirm vote for {candidate.name}?'):
            return
        self.controller.cast_vote(candidate.name)


class AdminFrame(BaseFrame):
    """Admin controls for managing candidates and the election."""
    def __init__(self, parent, controller: EVotingApp):
        super().__init__(parent, controller)
        tk.Label(self, text='Admin Panel', font=('Arial', 14)).pack(pady=8)
        tk.Button(self, text='Logout', command=controller.logout).pack(anchor='ne')

        control_frame = tk.Frame(self)
        control_frame.pack(pady=6)
        tk.Button(control_frame, text='Start Election', command=controller.start_election).grid(row=0, column=0, padx=4)
        tk.Button(control_frame, text='End Election', command=controller.end_election).grid(row=0, column=1, padx=4)
        tk.Button(control_frame, text='View Results', command=controller.view_results).grid(row=0, column=2, padx=4)

        tk.Label(self, text='Candidates').pack(pady=6)
        self.candidates_box = tk.Listbox(self, height=8, width=40)
        self.candidates_box.pack()

        add_frame = tk.Frame(self)
        add_frame.pack(pady=4)
        tk.Label(add_frame, text='Name').grid(row=0, column=0)
        self.name_entry = tk.Entry(add_frame)
        self.name_entry.grid(row=0, column=1)
        tk.Label(add_frame, text='Manifesto').grid(row=1, column=0)
        self.man_entry = tk.Entry(add_frame)
        self.man_entry.grid(row=1, column=1)
        tk.Button(add_frame, text='Add Candidate', command=self._add_candidate).grid(row=2, column=0, columnspan=2, pady=4)
        tk.Button(self, text='Remove Selected', command=self._remove_selected).pack(pady=3)

        self.bind('<<ShowFrame>>', self.on_show)

    def on_show(self, event):
        self.refresh_candidates()

    def refresh_candidates(self):
        self.candidates_box.delete(0, tk.END)
        for c in self.controller._election.get_candidates():
            self.candidates_box.insert(tk.END, f"{c.name} — {c.manifesto} ({c.votes} votes)")

    def _add_candidate(self):
        name = self.name_entry.get().strip()
        man = self.man_entry.get().strip()
        if not name:
            messagebox.showerror('Input Error', 'Candidate name required')
            return
        self.controller.add_candidate(name, man)
        self.name_entry.delete(0, tk.END)
        self.man_entry.delete(0, tk.END)
        self.refresh_candidates()

    def _remove_selected(self):
        sel = self.candidates_box.curselection()
        if not sel:
            messagebox.showerror('No Selection', 'Select candidate to remove')
            return
        index = sel[0]
        c = self.controller._election.get_candidates()[index]
        if not messagebox.askyesno('Confirm', f'Remove {c.name}?'):
            return
        self.controller.remove_candidate(c.name)
        self.refresh_candidates()


class ResultsFrame(BaseFrame):
    def __init__(self, parent, controller: EVotingApp):
        super().__init__(parent, controller)
        tk.Label(self, text='Election Results', font=('Arial', 14)).pack(pady=8)
        tk.Button(self, text='Back', command=lambda: controller.show_frame('LoginFrame')).pack(anchor='ne')
        self.results_box = tk.Listbox(self, height=12, width=60)
        self.results_box.pack(pady=10)

        self.bind('<<ShowFrame>>', self.on_show)

    def on_show(self, event):
        self.results_box.delete(0, tk.END)
        results = self.controller._election.get_results()
        if not results:
            self.results_box.insert(tk.END, 'No candidates or no votes yet')
            return
        sorted_res = sorted(results.items(), key=lambda t: t[1], reverse=True)
        for name, votes in sorted_res:
            self.results_box.insert(tk.END, f"{name}: {votes} votes")


# -------------------- Run --------------------
def main():
    election = Election()
    root = tk.Tk()
    app = EVotingApp(root, election)
    root.geometry('520x420')
    root.mainloop()


if __name__ == '__main__':
    main()
