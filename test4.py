"""
E-Voting System (Multi-department version)
Author: ChatGPT (modified)
Date: 2025-11-10

Features:
- GUI using Tkinter for voter registration, login, voting, and admin tasks
- Departments with separate candidates, plus top-level Guild President post
- Proper OOP: encapsulation, abstraction, inheritance, polymorphism
- Simple persistence to local JSON file (election_data.json)
- Password hashing with SHA-256
- Admin can manage departments, candidates, and start/stop elections
- Voters can register, login, and vote (department + guild president)
- GUI with improved colors and layout for better visual appeal

How to run: python e_voting_system.py
"""

import json
import os
import hashlib
import uuid
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


DATA_FILE = "election_data.json"

# --------------------------- Persistence ---------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "voters": {},
            "departments": {},  # department -> list of candidate dicts
            "votes": {},         # voter_id -> {"department": candidate_id, "guild": candidate_id}
            "election_open": False,
            "admin": {
                "username": "admin",
                "password_hash": hashlib.sha256("admin123".encode()).hexdigest()
            }
        }
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --------------------------- Domain Classes ---------------------------
class Person(ABC):
    def __init__(self, username):
        self._username = username

    @property
    def username(self):
        return self._username

    @abstractmethod
    def role(self):
        pass

class Voter(Person):
    def __init__(self, username, full_name, password_hash, department, voter_id=None):
        super().__init__(username)
        self._full_name = full_name
        self._password_hash = password_hash
        self._department = department
        self._voter_id = voter_id or str(uuid.uuid4())
        self._has_voted = False

    def role(self):
        return "voter"

    @property
    def full_name(self):
        return self._full_name

    @property
    def department(self):
        return self._department

    @property
    def voter_id(self):
        return self._voter_id

    def check_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest() == self._password_hash

    def to_dict(self):
        return {
            "username": self._username,
            "full_name": self._full_name,
            "password_hash": self._password_hash,
            "department": self._department,
            "voter_id": self._voter_id,
            "has_voted": self._has_voted
        }

    @staticmethod
    def from_dict(d):
        v = Voter(d["username"], d["full_name"], d["password_hash"], d["department"], d["voter_id"])
        v._has_voted = d.get("has_voted", False)
        return v

class Candidate:
    def __init__(self, name, manifesto="", department="guild"):
        self._candidate_id = str(uuid.uuid4())
        self._name = name
        self._manifesto = manifesto
        self._position = position 
        self._department = department

    @property
    def candidate_id(self):
        return self._candidate_id

    @property
    def name(self):
        return self._name

    @property
    def manifesto(self):
        return self._manifesto

    @property
    def department(self):
        return self._department
    
    @property
    def position(self):
        return self._position

    def to_dict(self):
        return {
            "candidate_id": self._candidate_id,
            "name": self._name,
            "manifesto": self._manifesto,
            "position": self._position,
            "department": self._department
        }

    @staticmethod
    def from_dict(d):
        c = Candidate(d["name"], d.get("manifesto", ""), d.get("position","department") ,d.get("department", ""))
        c._candidate_id = d["candidate_id"]
        return c

# --------------------------- Election Logic ---------------------------
class Election:
    def __init__(self):
        self._data = load_data()

    def admin_authenticate(self, username, password):
        admin = self._data.get("admin", {})
        return admin.get("username") == username and admin.get("password_hash") == hashlib.sha256(password.encode()).hexdigest()

    def start_election(self):
        self._data["election_open"] = True
        save_data(self._data)

    def stop_election(self):
        self._data["election_open"] = False
        save_data(self._data)

    def election_is_open(self):
        return self._data.get("election_open", False)

    def add_candidate(self, name, manifesto, department):
        c = Candidate(name, manifesto, department)
        self._data.setdefault("departments", {}).setdefault(department, []).append(c.to_dict())
        save_data(self._data)
        return c

    def list_candidates(self, department):
        dept_data = self._data.get("departments", {}).get(department, [])
        return [Candidate.from_dict(d) for d in dept_data]

    def list_all_candidates(self):
        # flatten all candidates
        out = []
        for dept, lst in self._data.get("departments", {}).items():
            for d in lst:
                out.append(Candidate.from_dict(d))
        return out

    def register_voter(self, username, full_name, department, password):
        if username in self._data["voters"]:
            raise ValueError("Username already exists")
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        v = Voter(username, full_name, pwd_hash, department)
        self._data["voters"][username] = v.to_dict()
        save_data(self._data)
        return v

    def authenticate_voter(self, username, password):
        d = self._data["voters"].get(username)
        if not d:
            raise ValueError("User not found")
        v = Voter.from_dict(d)
        if not v.check_password(password):
            raise ValueError("Invalid password")
        return v

    def cast_vote(self, voter, department_choice, guild_choice):
        if not self.election_is_open():
            raise RuntimeError("Election is closed")
        if voter.username not in self._data["voters"]:
            raise RuntimeError("Voter not registered")
        if self._data["voters"][voter.username]["has_voted"]:
            raise RuntimeError("Voter already voted")
        # record vote
        self._data.setdefault("votes", {})[voter.voter_id] = {
            "department": department_choice,
            "guild": guild_choice
        }
        self._data["voters"][voter.username]["has_voted"] = True
        save_data(self._data)

    def tally(self):
        # produce counts by candidate id and also by department grouping
        counts_by_candidate = {}
        candidate_info = {}
        for dept, lst in self._data.get("departments", {}).items():
            for c in lst:
                cid = c["candidate_id"]
                counts_by_candidate[cid] = 0
                candidate_info[cid] = {"name": c["name"], "department": c.get("department", dept)}
        for vote in self._data.get("votes", {}).values():
            dep_cid = vote.get("department")
            guild_cid = vote.get("guild")
            if dep_cid in counts_by_candidate:
                counts_by_candidate[dep_cid] += 1
            if guild_cid in counts_by_candidate:
                counts_by_candidate[guild_cid] += 1
        # organize into readable results
        results = {"by_candidate": [], "by_department": {}}
        for cid, cnt in counts_by_candidate.items():
            info = candidate_info.get(cid, {})
            results["by_candidate"].append({"candidate_id": cid, "name": info.get("name"), "department": info.get("department"), "votes": cnt})
            # department totals
            dept = info.get("department", "guild")
            results["by_department"][dept] = results["by_department"].get(dept, 0) + cnt
        # sort candidate list
        results["by_candidate"].sort(key=lambda x: x["votes"], reverse=True)
        return results

# --------------------------- GUI ---------------------------
class ElectionApp(tk.Tk):
    def __init__(self, election):
        super().__init__()
        self.election = election
        self.current_user = None
        self.is_admin_logged_in = False 

        self.title("University E-Voting System")
        self.geometry("900x600")
        self.configure(bg="#f0f8ff")

        self._create_navbar()
        self.container = tk.Frame(self, bg="#e6f2ff")
        self.container.pack(fill=tk.BOTH, expand=True)

        self.show_home()

    def _create_navbar(self):
        nav = tk.Frame(self, bg="#4682b4", height=50)
        nav.pack(fill=tk.X)
        btn_specs = [("Home", self.show_home), ("Register", self.show_register), ("Login", self.show_login), ("Admin", self.show_admin_login)]
        for text, cmd in btn_specs:
            b = tk.Button(nav, text=text, command=cmd, bg="#5f9ea0", fg="white", relief=tk.FLAT, padx=10, pady=8)
            b.pack(side=tk.LEFT, padx=6, pady=6)

    def clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def show_home(self):
        self.clear_container()
        tk.Label(self.container, text="Welcome to the University E-Voting System", bg="#e6f2ff", fg="#003366", font=("Arial", 20, "bold")).pack(pady=20)
        state = "OPEN" if self.election.election_is_open() else "CLOSED"
        tk.Label(self.container, text=f"Election status: {state}", bg="#e6f2ff", fg="#333", font=("Arial", 14)).pack(pady=5)

        # show guild candidates prominently
        tk.Label(self.container, text="Guild President Candidates:", bg="#e6f2ff", fg="#222", font=("Arial", 14, "underline")).pack(pady=8)
        guild = self.election.list_candidates("guild")
        if not guild:
            tk.Label(self.container, text="No guild candidates yet.", bg="#e6f2ff").pack()
        else:
            for c in guild:
                frame = tk.Frame(self.container, bg="#ffffff", bd=1, relief=tk.RIDGE, padx=8, pady=6)
                frame.pack(fill=tk.X, padx=20, pady=4)
                tk.Label(frame, text=c.name, bg="#ffffff", font=("Arial", 12, "bold")).pack(anchor=tk.W)
                tk.Label(frame, text=f"Manifesto: {c.manifesto}", bg="#ffffff").pack(anchor=tk.W)

    def show_register(self):
        self.clear_container()
        tk.Label(self.container, text="Voter Registration", bg="#e6f2ff", font=("Arial", 16, "bold"), fg="#004080").pack(pady=10)
        frame = tk.Frame(self.container, bg="#e6f2ff")
        frame.pack(pady=10)

        tk.Label(frame, text="Full Name", bg="#e6f2ff").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = tk.Entry(frame, width=40)
        name_entry.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Username", bg="#e6f2ff").grid(row=1, column=0, sticky=tk.W, pady=5)
        user_entry = tk.Entry(frame, width=40)
        user_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Department", bg="#e6f2ff").grid(row=2, column=0, sticky=tk.W, pady=5)
        dept_entry = tk.Entry(frame, width=40)
        dept_entry.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Password", bg="#e6f2ff").grid(row=3, column=0, sticky=tk.W, pady=5)
        pwd_entry = tk.Entry(frame, show="*", width=40)
        pwd_entry.grid(row=3, column=1, pady=5)

        def do_register():
            try:
                name = name_entry.get().strip()
                user = user_entry.get().strip()
                dept = dept_entry.get().strip() or "general"
                pwd = pwd_entry.get().strip()
                if not (name and user and pwd):
                    raise ValueError("Name, username and password are required")
                v = self.election.register_voter(user, name, dept, pwd)
                messagebox.showinfo("Registered", f"Welcome {v.full_name}! You can now login.")
                self.show_login()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(self.container, text="Register", command=do_register, bg="#4682b4", fg="white", padx=10).pack(pady=10)

    def show_login(self):
        self.clear_container()
        tk.Label(self.container, text="Voter Login", bg="#e6f2ff", font=("Arial", 16, "bold"), fg="#004080").pack(pady=10)
        frame = tk.Frame(self.container, bg="#e6f2ff")
        frame.pack(pady=10)

        tk.Label(frame, text="Username", bg="#e6f2ff").grid(row=0, column=0, sticky=tk.W, pady=5)
        user_entry = tk.Entry(frame, width=40)
        user_entry.grid(row=0, column=1)
        tk.Label(frame, text="Password", bg="#e6f2ff").grid(row=1, column=0, sticky=tk.W, pady=5)
        pwd_entry = tk.Entry(frame, show="*", width=40)
        pwd_entry.grid(row=1, column=1)

        def do_login():
            try:
                v = self.election.authenticate_voter(user_entry.get().strip(), pwd_entry.get().strip())
                self.current_user = v
                messagebox.showinfo("Welcome", f"Logged in as {v.full_name}")
                self.show_vote_screen()
            except Exception as e:
                messagebox.showerror("Login Failed", str(e))

        tk.Button(self.container, text="Login", command=do_login, bg="#4682b4", fg="white", padx=10).pack(pady=10)

    def show_vote_screen(self):
        self.clear_container()
        v = self.current_user
        if not v:
            return messagebox.showerror("Error", "Login first")

        if not self.election.election_is_open():
            tk.Label(self.container, text="Election is CLOSED", bg="#e6f2ff", fg="red").pack(pady=10)
            return

        if self.election._data["voters"][v.username]["has_voted"]:
            tk.Label(self.container, text="You already voted!", bg="#e6f2ff", fg="#006400").pack(pady=10)
            return

        tk.Label(self.container, text=f"Welcome {v.full_name}", bg="#e6f2ff", fg="#003366", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(self.container, text=f"Vote for your department ({v.department}) representative:", bg="#e6f2ff").pack(pady=5)
        dept_var = tk.StringVar()
        dept_candidates = self.election.list_candidates(v.department)
        if not dept_candidates:
            tk.Label(self.container, text="No candidates in your department yet.", bg="#e6f2ff").pack()
        else:
            for c in dept_candidates:
                tk.Radiobutton(self.container, text=f"{c.name} - {c.manifesto}", variable=dept_var, value=c.candidate_id, bg="#e6f2ff", anchor="w").pack(fill=tk.X, padx=20)

        tk.Label(self.container, text="\nVote for Guild President:", bg="#e6f2ff").pack(pady=5)
        guild_var = tk.StringVar()
        guild_candidates = self.election.list_candidates("guild")
        if not guild_candidates:
            tk.Label(self.container, text="No guild candidates yet.", bg="#e6f2ff").pack()
        else:
            for c in guild_candidates:
                tk.Radiobutton(self.container, text=f"{c.name} - {c.manifesto}", variable=guild_var, value=c.candidate_id, bg="#e6f2ff", anchor="w").pack(fill=tk.X, padx=20)

        def submit_vote():
            try:
                if not (dept_var.get() and guild_var.get()):
                    raise ValueError("Select both department and guild candidates before submitting")
                self.election.cast_vote(v, dept_var.get(), guild_var.get())
                messagebox.showinfo("Vote Recorded", "Your vote was successfully submitted.")
                self.show_home()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(self.container, text="Submit Vote", command=submit_vote, bg="#00688B", fg="white", padx=10).pack(pady=12)

    def show_admin_login(self):
        self.clear_container()
        tk.Label(self.container, text="Admin Login", bg="#e6f2ff", font=("Arial", 16, "bold"), fg="#004080").pack(pady=10)
        frame = tk.Frame(self.container, bg="#e6f2ff")
        frame.pack(pady=10)

        tk.Label(frame, text="Username", bg="#e6f2ff").grid(row=0, column=0, sticky=tk.W)
        user_entry = tk.Entry(frame, width=40)
        user_entry.grid(row=0, column=1, pady=5)
        tk.Label(frame, text="Password", bg="#e6f2ff").grid(row=1, column=0, sticky=tk.W)
        pwd_entry = tk.Entry(frame, show="*", width=40)
        pwd_entry.grid(row=1, column=1, pady=5)

        def do_login():
            username = user_entry.get().strip()
            password = pwd_entry.get().strip()

            if self.election.admin_authenticate(username, password):
                self.is_admin_logged_in = True   # mark that admin is now logged in
                messagebox.showinfo("Admin", "Welcome, admin!")
                self.show_admin_panel()
            else:
                self.is_admin_logged_in = False  # ensure flag is reset if login fails
                messagebox.showerror("Failed", "Invalid credentials")

        tk.Button(self.container, text="Login", command=do_login, bg="#4682b4", fg="white", padx=10).pack(pady=10)

    def show_admin_panel(self):
        self.clear_container()
        tk.Label(self.container, text="Admin Panel", bg="#e6f2ff", fg="#003366", font=("Arial", 16, "bold")).pack(pady=10)

        def add_candidate():
            dept = simpledialog.askstring("Department", "Enter department name (or 'guild' for president):", parent=self)
            if not dept:
                return
            name = simpledialog.askstring("Candidate Name", "Enter candidate name:", parent=self)
            if not name:
                return
            manifesto = simpledialog.askstring("Manifesto", "Enter manifesto:", parent=self)
            self.election.add_candidate(name, manifesto or "", dept)
            messagebox.showinfo("Success", f"Added {name} to {dept}")
            self.show_admin_panel()

        tk.Button(self.container, text="Add Candidate", command=add_candidate, bg="#4682b4", fg="white", padx=10).pack(pady=6)

        ctrl_frame = tk.Frame(self.container, bg="#e6f2ff")
        ctrl_frame.pack(pady=6)
        tk.Button(ctrl_frame, text="Start Election", command=lambda: [self.election.start_election(), messagebox.showinfo("Election", "Election started"), self.show_admin_panel()], bg="#228B22", fg="white", padx=10).grid(row=0, column=0, padx=6)
        tk.Button(ctrl_frame, text="Stop Election", command=lambda: [self.election.stop_election(), messagebox.showinfo("Election", "Election stopped"), self.show_admin_panel()], bg="#8B0000", fg="white", padx=10).grid(row=0, column=1, padx=6)

        # show departments and their candidates
        tk.Label(self.container, text="\nDepartments and Candidates:", bg="#e6f2ff", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10)
        for dept, lst in self.election._data.get("departments", {}).items():
            frame = tk.Frame(self.container, bg="#ffffff", bd=1, relief=tk.SOLID, padx=6, pady=6)
            frame.pack(fill=tk.X, padx=12, pady=4)
            tk.Label(frame, text=dept, bg="#ffffff", font=("Arial", 12, "bold")).pack(anchor=tk.W)
            for c in lst:
                tk.Label(frame, text=f"{c['name']} — {c.get('manifesto','')}", bg="#ffffff").pack(anchor=tk.W, padx=6)
                
        # 🔒 Only visible to admin: view results
        ttk.Button(self.container, text="View Election Results", command=self.show_results).pack(pady=5)

        tk.Button(self.container, text="Back to Home", command=self.show_home, bg="#4682b4", fg="white", padx=10).pack(pady=12)

    def show_results(self):
        self.clear_container()
        tk.Label(self.container, text="Election Results", bg="#e6f2ff",
            font=("Arial", 16, "bold"), fg="#004080").pack(pady=10)

    # Restrict to admin only
        if not self.is_admin_logged_in:
            messagebox.showerror("Access Denied", "Only the admin can view results.")
            return

        res = self.election.tally()
        if not res["by_candidate"]:
            tk.Label(self.container, text="No results yet.", bg="#e6f2ff").pack(pady=6)
            ttk.Button(self.container, text="Back", command=self.show_admin_panel).pack(pady=10)
            return

    # Separate candidates by position
        guild_candidates = [c for c in res["by_candidate"] if c['position'] == 'guild']
        dept_candidates = [c for c in res["by_candidate"] if c['position'] != 'guild']

    # --- Text summary ---
        tk.Label(self.container, text="Guild President Results:", bg="#e6f2ff",
             font=("Arial", 12, "bold")).pack(pady=6)
        for c in guild_candidates:
            tk.Label(
                self.container,
                text=f"{c['name']}: {c['votes']} votes",
                bg="#e6f2ff"
            ).pack(anchor=tk.W, padx=10)

        tk.Label(self.container, text="\nDepartment Results:", bg="#e6f2ff",
             font=("Arial", 12, "bold")).pack(pady=6)
        for c in dept_candidates:
            tk.Label(
                self.container,
                text=f"{c['name']} ({c['department']}): {c['votes']} votes",
                bg="#e6f2ff"
            ).pack(anchor=tk.W, padx=10)

    # --- Graphs ---
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # --- Guild President Graph ---
            if guild_candidates:
                names = [c['name'] for c in guild_candidates]
                votes = [c['votes'] for c in guild_candidates]
                fig1 = Figure(figsize=(6, 2.5), dpi=100)
                ax1 = fig1.add_subplot(111)
                ax1.bar(names, votes, color="#ff6666")
                ax1.set_title("Guild President Votes")
                ax1.set_ylabel("Votes")
                ax1.tick_params(axis='x', rotation=30)
                canvas1 = FigureCanvasTkAgg(fig1, master=self.container)
                canvas1.draw()
                canvas1.get_tk_widget().pack(pady=6)

        # --- Department Graph ---
            if dept_candidates:
                names = [c['name'] for c in dept_candidates]
                votes = [c['votes'] for c in dept_candidates]
                fig2 = Figure(figsize=(6, 3), dpi=100)
                ax2 = fig2.add_subplot(111)
                ax2.bar(names, votes, color="#0073e6")
                ax2.set_title("Department Votes")
                ax2.set_ylabel("Votes")
                ax2.tick_params(axis='x', rotation=30)
                canvas2 = FigureCanvasTkAgg(fig2, master=self.container)
                canvas2.draw()
                canvas2.get_tk_widget().pack(pady=6)

        except ImportError:
            tk.Label(self.container, text="Matplotlib not installed — graphs unavailable.", bg="#e6f2ff", fg="red").pack()

    # Back button
        ttk.Button(self.container, text="Back", command=self.show_admin_panel).pack(pady=10)

#---------------------- RUN ------------------------
if __name__ == "__main__":
    election = Election()
    # sample data seed
    if not election.list_candidates("guild"):
        election.add_candidate("Alice N.", "Transparency and student welfare", "guild")
        election.add_candidate("Brian K.", "Sports and tech development", "guild")
    # example departments
    if not election.list_candidates("Computer Science"):
        election.add_candidate("Cathy C.", "Improve labs", "Computer Science")
        election.add_candidate("Daniel D.", "Student mentorship", "Computer Science")
    app = ElectionApp(election)
    app.mainloop()
