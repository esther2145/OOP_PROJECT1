"""
E-Voting System (Single-file)
Author: ChatGPT
Date: 2025-11-03

Features:
- GUI using Tkinter for voter registration, login, voting, and admin tasks
- Proper OOP: encapsulation, abstraction, inheritance, polymorphism
- Simple persistence to local JSON file (data.json)
- Password hashing with SHA-256 (not production secure but fine for demo)
- Admin can create candidates, start/stop election, view results
- Voters can register, login, and cast a single vote

How to run: python e_voting_system.py

Notes:
- This is an educational prototype, not secure for real elections.
- For real deployments: secure authentication, cryptographic ballots, audit logs,
  networked backend, and legal compliance are required.
"""

import json
import os
import hashlib
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# --------------------------- Persistence Utilities ---------------------------
DATA_FILE = "election_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "voters": {},          # voter_id -> voter dict
            "candidates": {},      # candidate_id -> candidate dict
            "votes": {},           # voter_id -> candidate_id
            "election_open": False,
            "admin": {
                "username": "admin",
                "password_hash": hashlib.sha256("admin".encode()).hexdigest()
            }
        }
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --------------------------- Domain Model (OOP) ---------------------------

class Person(ABC):
    """Abstract base class representing a person interacting with the system.

    Demonstrates Abstraction: Person defines a public interface; concrete
    person types implement details.
    """

    def __init__(self, username: str):
        self._username = username  # encapsulated attribute

    @property
    def username(self):
        return self._username

    @abstractmethod
    def role(self) -> str:
        pass


class Voter(Person):
    """Represents a voter. Shows Inheritance from Person and Encapsulation of state."""

    def __init__(self, username: str, full_name: str, password_hash: str, voter_id: str = None):
        super().__init__(username)
        self._full_name = full_name
        self._password_hash = password_hash
        self._voter_id = voter_id or str(uuid.uuid4())
        self._has_voted = False

    def role(self) -> str:
        return "voter"

    @property
    def voter_id(self):
        return self._voter_id

    @property
    def full_name(self):
        return self._full_name

    def check_password(self, password: str) -> bool:
        return hashlib.sha256(password.encode()).hexdigest() == self._password_hash

    def mark_voted(self):
        self._has_voted = True

    def has_voted(self) -> bool:
        return self._has_voted

    def to_dict(self):
        return {
            "username": self._username,
            "full_name": self._full_name,
            "password_hash": self._password_hash,
            "voter_id": self._voter_id,
            "has_voted": self._has_voted
        }

    @staticmethod
    def from_dict(d):
        v = Voter(d["username"], d["full_name"], d["password_hash"], d["voter_id"])
        v._has_voted = d.get("has_voted", False)
        return v


class Candidate:
    """Simple data holder for a candidate."""

    def __init__(self, name: str, manifesto: str = ""):
        self._candidate_id = str(uuid.uuid4())
        self._name = name
        self._manifesto = manifesto

    @property
    def candidate_id(self):
        return self._candidate_id

    @property
    def name(self):
        return self._name

    @property
    def manifesto(self):
        return self._manifesto

    def to_dict(self):
        return {"candidate_id": self._candidate_id, "name": self._name, "manifesto": self._manifesto}

    @staticmethod
    def from_dict(d):
        c = Candidate(d["name"], d.get("manifesto", ""))
        c._candidate_id = d["candidate_id"]
        return c


class Election:
    """Core election logic. Encapsulates state and provides a clear API.

    Demonstrates Polymorphism: different Person types interact with Election via known methods.
    """

    def __init__(self):
        self._data = load_data()
        self._voters: Dict[str, Dict] = self._data.get("voters", {})
        self._candidates: Dict[str, Dict] = self._data.get("candidates", {})
        self._votes: Dict[str, str] = self._data.get("votes", {})
        self._election_open: bool = self._data.get("election_open", False)

    # ---------- Admin / Election control ----------
    def admin_authenticate(self, username: str, password: str) -> bool:
        admin = self._data.get("admin", {})
        return admin.get("username") == username and admin.get("password_hash") == hashlib.sha256(password.encode()).hexdigest()

    def set_admin_password(self, new_password: str):
        self._data.setdefault("admin", {})["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
        save_data(self._data)

    def start_election(self):
        self._election_open = True
        self._data["election_open"] = True
        save_data(self._data)

    def stop_election(self):
        self._election_open = False
        self._data["election_open"] = False
        save_data(self._data)

    def election_is_open(self) -> bool:
        return self._election_open

    # ---------- Candidates management ----------
    def add_candidate(self, name: str, manifesto: str = "") -> Candidate:
        c = Candidate(name, manifesto)
        self._candidates[c.candidate_id] = c.to_dict()
        self._data["candidates"] = self._candidates
        save_data(self._data)
        return c

    def list_candidates(self) -> List[Candidate]:
        return [Candidate.from_dict(d) for d in self._candidates.values()]

    # ---------- Voter registration & authentication ----------
    def register_voter(self, username: str, full_name: str, password: str) -> Voter:
        if username in self._voters:
            raise ValueError("Username already exists")
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        v = Voter(username, full_name, pwd_hash)
        self._voters[username] = v.to_dict()
        self._data["voters"] = self._voters
        save_data(self._data)
        return v

    def authenticate_voter(self, username: str, password: str) -> Voter:
        d = self._voters.get(username)
        if not d:
            raise ValueError("Voter not found")
        v = Voter.from_dict(d)
        if not v.check_password(password):
            raise ValueError("Incorrect password")
        return v

    # ---------- Voting ----------
    def cast_vote(self, voter: Voter, candidate_id: str) -> None:
        if not self._election_open:
            raise RuntimeError("Election is not open")
        if voter.username not in self._voters:
            raise RuntimeError("Voter not registered")
        # reload voter record to check if already voted
        voter_record = Voter.from_dict(self._voters[voter.username])
        if voter_record.has_voted():
            raise RuntimeError("Voter has already cast a vote")
        if candidate_id not in self._candidates:
            raise RuntimeError("Invalid candidate")
        self._votes[voter.voter_id] = candidate_id
        # mark and persist
        self._voters[voter.username]["has_voted"] = True
        self._data["votes"] = self._votes
        self._data["voters"] = self._voters
        save_data(self._data)

    def tally(self) -> Dict[str, int]:
        counts: Dict[str, int] = {cid: 0 for cid in self._candidates.keys()}
        for cid in self._votes.values():
            counts[cid] = counts.get(cid, 0) + 1
        return counts

    def results_readable(self) -> List[Dict]:
        counts = self.tally()
        out = []
        for cid, data in self._candidates.items():
            out.append({
                "candidate_id": cid,
                "name": data["name"],
                "votes": counts.get(cid, 0)
            })
        # sort by votes desc
        out.sort(key=lambda x: x["votes"], reverse=True)
        return out


# --------------------------- GUI Application ---------------------------

class ElectionApp(tk.Tk):
    """Tkinter-based GUI. Modular design with methods for each screen.

    Demonstrates clean separation of concerns: UI code orchestrates Election model.
    """

    def __init__(self, election: Election):
        super().__init__()
        self.title("E-Voting System — Student Council Election")
        self.geometry("700x500")
        self.resizable(False, False)

        self.election = election
        self.current_user: Voter | None = None

        # create main containers
        self._create_widgets()
        self.show_home()

    def _create_widgets(self):
        # Navbar frame
        self.navbar = ttk.Frame(self)
        self.navbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_home = ttk.Button(self.navbar, text="Home", command=self.show_home)
        self.btn_home.pack(side=tk.LEFT, padx=4, pady=4)

        self.btn_register = ttk.Button(self.navbar, text="Register", command=self.show_register)
        self.btn_register.pack(side=tk.LEFT, padx=4)

        self.btn_login = ttk.Button(self.navbar, text="Login", command=self.show_login)
        self.btn_login.pack(side=tk.LEFT, padx=4)

        self.btn_admin = ttk.Button(self.navbar, text="Admin", command=self.show_admin_login)
        self.btn_admin.pack(side=tk.RIGHT, padx=4)

        # Main content frame
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill=tk.BOTH, expand=True)

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ------------------- Screens -------------------
    def show_home(self):
        self.clear_container()
        lbl = ttk.Label(self.container, text="Welcome to the Student Council E-Voting System", font=(None, 16))
        lbl.pack(pady=10)

        subtitle = ttk.Label(self.container, text="Mission: Choose leaders who represent your voice."
                            )
        subtitle.pack(pady=6)

        status = "OPEN" if self.election.election_is_open() else "CLOSED"
        status_lbl = ttk.Label(self.container, text=f"Election status: {status}")
        status_lbl.pack(pady=4)

        # show candidates and current tally (if any)
        candidates = self.election.list_candidates()
        if not candidates:
            ttk.Label(self.container, text="No candidates registered yet.").pack(pady=6)
        else:
            ttk.Label(self.container, text="Candidates:").pack(pady=6)
            for c in candidates:
                frame = ttk.Frame(self.container, relief=tk.RIDGE, padding=6)
                frame.pack(fill=tk.X, pady=3)
                ttk.Label(frame, text=c.name, font=(None, 12, "bold")).pack(anchor=tk.W)
                ttk.Label(frame, text=f"Manifesto: {c.manifesto}").pack(anchor=tk.W)

        ttk.Button(self.container, text="View Results", command=self.show_results).pack(pady=10)

    def show_register(self):
        self.clear_container()
        ttk.Label(self.container, text="Voter Registration", font=(None, 14)).pack(pady=6)

        frm = ttk.Frame(self.container)
        frm.pack(pady=6)

        ttk.Label(frm, text="Full name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        name_entry = ttk.Entry(frm, width=40)
        name_entry.grid(row=0, column=1, pady=2)

        ttk.Label(frm, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=2)
        user_entry = ttk.Entry(frm, width=40)
        user_entry.grid(row=1, column=1, pady=2)

        ttk.Label(frm, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=2)
        pwd_entry = ttk.Entry(frm, show="*", width=40)
        pwd_entry.grid(row=2, column=1, pady=2)

        def do_register():
            name = name_entry.get().strip()
            username = user_entry.get().strip()
            pwd = pwd_entry.get().strip()
            try:
                if not (name and username and pwd):
                    raise ValueError("Please fill all fields")
                v = self.election.register_voter(username, name, pwd)
                messagebox.showinfo("Success", f"Registered {v.full_name}. Your Voter ID: {v.voter_id}")
                self.show_login()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(self.container, text="Register", command=do_register).pack(pady=8)

    def show_login(self):
        self.clear_container()
        ttk.Label(self.container, text="Voter Login", font=(None, 14)).pack(pady=6)

        frm = ttk.Frame(self.container)
        frm.pack(pady=6)

        ttk.Label(frm, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        user_entry = ttk.Entry(frm, width=40)
        user_entry.grid(row=0, column=1, pady=2)

        ttk.Label(frm, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        pwd_entry = ttk.Entry(frm, show="*", width=40)
        pwd_entry.grid(row=1, column=1, pady=2)

        def do_login():
            username = user_entry.get().strip()
            pwd = pwd_entry.get().strip()
            try:
                v = self.election.authenticate_voter(username, pwd)
                self.current_user = v
                messagebox.showinfo("Welcome", f"Hello {v.full_name}! Logged in.")
                self.show_vote_screen()
            except Exception as e:
                messagebox.showerror("Login failed", str(e))

        ttk.Button(self.container, text="Login", command=do_login).pack(pady=8)

    def show_vote_screen(self):
        if not self.current_user:
            messagebox.showerror("Error", "No user logged in")
            return
        self.clear_container()
        ttk.Label(self.container, text=f"Hello {self.current_user.full_name}", font=(None, 14)).pack(pady=6)
        if self.election.election_is_open() is False:
            ttk.Label(self.container, text="The election is currently CLOSED. Please wait for it to open.").pack(pady=6)
            return

        if self.election._voters[self.current_user.username].get("has_voted"):
            ttk.Label(self.container, text="You have already voted. Thank you!").pack(pady=6)
            return

        ttk.Label(self.container, text="Please choose a candidate:").pack(pady=6)
        candidates = self.election.list_candidates()

        choice_var = tk.StringVar()

        for c in candidates:
            ttk.Radiobutton(self.container, text=f"{c.name} — {c.manifesto}", variable=choice_var, value=c.candidate_id).pack(anchor=tk.W, padx=10)

        def submit_vote():
            cid = choice_var.get()
            if not cid:
                messagebox.showerror("Error", "Select a candidate")
                return
            try:
                self.election.cast_vote(self.current_user, cid)
                messagebox.showinfo("Vote recorded", "Your vote has been recorded — thank you for participating!")
                self.show_home()
            except Exception as e:
                messagebox.showerror("Cannot vote", str(e))

        ttk.Button(self.container, text="Submit Vote", command=submit_vote).pack(pady=8)

    def show_results(self):
        self.clear_container()
        ttk.Label(self.container, text="Election Results", font=(None, 14)).pack(pady=6)
        rows = self.election.results_readable()
        if not rows:
            ttk.Label(self.container, text="No candidates or votes yet.").pack(pady=6)
            return
        for r in rows:
            ttk.Label(self.container, text=f"{r['name']}: {r['votes']} votes").pack(anchor=tk.W, padx=8)

    # ------------------- Admin UI -------------------
    def show_admin_login(self):
        self.clear_container()
        ttk.Label(self.container, text="Admin Login", font=(None, 14)).pack(pady=6)

        frm = ttk.Frame(self.container)
        frm.pack(pady=6)
        ttk.Label(frm, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        user_entry = ttk.Entry(frm, width=40)
        user_entry.grid(row=0, column=1, pady=2)
        ttk.Label(frm, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        pwd_entry = ttk.Entry(frm, show="*", width=40)
        pwd_entry.grid(row=1, column=1, pady=2)

        def do_admin_login():
            username = user_entry.get().strip()
            pwd = pwd_entry.get().strip()
            if self.election.admin_authenticate(username, pwd):
                messagebox.showinfo("Admin", "Welcome, admin")
                self.show_admin_panel()
            else:
                messagebox.showerror("Failed", "Invalid admin credentials")

        ttk.Button(self.container, text="Login", command=do_admin_login).pack(pady=8)

    def show_admin_panel(self):
        self.clear_container()
        ttk.Label(self.container, text="Admin Panel", font=(None, 14)).pack(pady=6)

        # Election controls
        frm = ttk.Frame(self.container)
        frm.pack(pady=4)
        state = "OPEN" if self.election.election_is_open() else "CLOSED"
        lbl = ttk.Label(frm, text=f"Election is currently: {state}")
        lbl.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        def start_election():
            self.election.start_election()
            messagebox.showinfo("Election", "Election started")
            self.show_admin_panel()

        def stop_election():
            self.election.stop_election()
            messagebox.showinfo("Election", "Election stopped")
            self.show_admin_panel()

        ttk.Button(frm, text="Start Election", command=start_election).grid(row=1, column=0, pady=6, padx=6)
        ttk.Button(frm, text="Stop Election", command=stop_election).grid(row=1, column=1, pady=6, padx=6)

        # Candidate management
        ttk.Separator(self.container, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        ttk.Label(self.container, text="Candidates Management", font=(None, 12)).pack(pady=4)

        def add_candidate_ui():
            name = simpledialog.askstring("Candidate name", "Enter candidate name:", parent=self)
            if not name:
                return
            manifesto = simpledialog.askstring("Manifesto", "Enter a short manifesto (optional):", parent=self)
            self.election.add_candidate(name, manifesto or "")
            messagebox.showinfo("Added", f"Candidate '{name}' added")
            self.show_admin_panel()

        ttk.Button(self.container, text="Add Candidate", command=add_candidate_ui).pack(pady=6)

        # Show candidates
        cframe = ttk.Frame(self.container)
        cframe.pack(fill=tk.BOTH, expand=True)
        ttk.Label(cframe, text="Candidates:").pack(anchor=tk.W)
        candidates = self.election.list_candidates()
        for c in candidates:
            ttk.Label(cframe, text=f"{c.name} — {c.manifesto}").pack(anchor=tk.W, padx=8)

        ttk.Button(self.container, text="View Full Results", command=self.show_results).pack(pady=8)


# --------------------------- Run Application ---------------------------

if __name__ == "__main__":
    election = Election()
    # create sample data if none exists
    if not election.list_candidates():
        election.add_candidate("Alice N.", "Transparency and student welfare")
        election.add_candidate("Brian K.", "Sports and tech development")
    app = ElectionApp(election)
    app.mainloop()
