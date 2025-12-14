from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

from datetime import datetime, timedelta
import random
import math
import copy
import threading

class TransportOptimizerApp(App):
    def build(self):
        self.title = "🔥 Simulated Annealing Transport Scheduler"
        # Removed theme_cls line to fix AttributeError
        Window.clearcolor = (0.1, 0.1, 0.2, 1)  # Dark background
        
        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Header
        header = Label(
            text='[color=00ff00][b]🔥 SIMULATED ANNEALING\nEMPLOYEE TRANSPORT SCHEDULER[/b][/color]',
            markup=True,
            size_hint_y=None,
            height=dp(80),
            font_size='20sp',
            halign='center'
        )
        main_layout.add_widget(header)
        
        # Input Section
        input_section = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(300))
        
        # Bus Details
        bus_layout = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(80))
        bus_layout.add_widget(Label(text='🚌 Bus Capacity:', size_hint_y=None, height=dp(40)))
        self.bus_capacity = TextInput(text='22', multiline=False, input_filter='int', size_hint_y=None, height=dp(40))
        bus_layout.add_widget(self.bus_capacity)
        bus_layout.add_widget(Label(text='🚌 Max Trips:', size_hint_y=None, height=dp(40)))
        self.max_trips = TextInput(text='5', multiline=False, input_filter='int', size_hint_y=None, height=dp(40))
        bus_layout.add_widget(self.max_trips)
        input_section.add_widget(bus_layout)
        
        # Companies Section
        companies_section = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(100))
        companies_section.add_widget(Label(text='🏢 Number of Companies:', size_hint_y=None, height=dp(30)))
        self.num_companies = TextInput(text='3', multiline=False, input_filter='int', size_hint_y=None, height=dp(40))
        companies_section.add_widget(self.num_companies)
        input_section.add_widget(companies_section)
        
        main_layout.add_widget(input_section)
        
        # Action Buttons
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        self.add_companies_btn = Button(text='➕ Add Companies Data', size_hint_y=None, height=dp(50))
        self.add_companies_btn.bind(on_press=self.show_companies_popup)
        self.optimize_btn = Button(text='🚀 OPTIMIZE ROUTE', background_color=(0.2, 0.8, 0.2, 1), size_hint_y=None, height=dp(50))
        self.optimize_btn.bind(on_press=self.run_optimization)
        btn_layout.add_widget(self.add_companies_btn)
        btn_layout.add_widget(self.optimize_btn)
        main_layout.add_widget(btn_layout)
        
        # Progress Section
        self.progress_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(60))
        self.progress_bar = ProgressBar(max=1000, value=0, size_hint_y=None, height=dp(30))
        self.status_label = Label(text='Ready to optimize...', size_hint_y=None, height=dp(30))
        self.progress_layout.add_widget(self.progress_bar)
        self.progress_layout.add_widget(self.status_label)
        main_layout.add_widget(self.progress_layout)
        
        # Results Section
        self.results_scroll = ScrollView()
        self.results_label = Label(
            text='Results will appear here...',
            size_hint_y=None,
            height=dp(400),
            halign='left',
            valign='top',
            text_size=(None, None),
            markup=True
        )
        self.results_label.bind(texture_size=self.results_label.setter('size'))
        self.results_scroll.add_widget(self.results_label)
        main_layout.add_widget(self.results_scroll)
        
        # Data Storage
        self.companies_data = []
        self.employees = {}
        self.route_distance = {}
        
        return main_layout
   
    def show_companies_popup(self, instance):
        content = GridLayout(cols=1, spacing=dp(10), padding=dp(20))
        
        scroll = ScrollView(size_hint=(1, 0.7))
        companies_grid = GridLayout(cols=3, spacing=dp(5), size_hint_y=None)
        companies_grid.bind(minimum_height=companies_grid.setter('height'))
        
        self.companies_inputs = []
        num_companies = int(self.num_companies.text or 0)
        for i in range(num_companies):
            name_input = TextInput(hint_text=f'Company {i+1}', multiline=False, size_hint_y=None, height=dp(40))
            emp_input = TextInput(hint_text='Employees', multiline=False, input_filter='int', size_hint_y=None, height=dp(40))
            dist_input = TextInput(hint_text='Distance (km)', multiline=False, input_filter='float', size_hint_y=None, height=dp(40))
            
            self.companies_inputs.extend([name_input, emp_input, dist_input])
            companies_grid.add_widget(name_input)
            companies_grid.add_widget(emp_input)
            companies_grid.add_widget(dist_input)
        
        scroll.add_widget(companies_grid)
        content.add_widget(scroll)
        
        save_btn = Button(text='💾 Save Companies Data', size_hint_y=None, height=dp(50))
        save_btn.bind(on_press=lambda x: self.save_companies_data())
        content.add_widget(save_btn)
        
        popup = Popup(title='🏢 Enter Companies Data (Route Order)', content=content, size_hint=(0.9, 0.9))
        popup.open()
        return popup  # Return popup for proper dismissal
    
    def save_companies_data(self):
        self.companies_data = []
        self.employees = {}
        self.route_distance = {}
        
        num_inputs = len(self.companies_inputs)
        for i in range(0, num_inputs, 3):
            if i + 2 < num_inputs:
                name = self.companies_inputs[i].text.strip()
                emp = int(self.companies_inputs[i+1].text or 0)
                dist = float(self.companies_inputs[i+2].text or 0)
                
                if name:
                    self.companies_data.append(name)
                    self.employees[name] = emp
                    self.route_distance[name] = dist
        
        self.results_label.text = f'✅ Saved {len(self.companies_data)} companies\nTotal employees: {sum(self.employees.values())}'
        
        # Close popup safely
        if hasattr(self, 'current_popup') and self.current_popup:
            self.current_popup.dismiss()
    
    def run_optimization(self, instance):
        if not self.companies_data:
            self.results_label.text = '[color=ff4444]❌ Please add companies data first![/color]'
            return
        
        # Run optimization in background thread
        threading.Thread(target=self.optimize_background, daemon=True).start()
    
    def optimize_background(self):
        Clock.schedule_once(lambda dt: self.update_status('🔬 Running Simulated Annealing...', 0), 0)
        
        bus_capacity = int(self.bus_capacity.text or 22)
        max_trips = int(self.max_trips.text or 5)
        
        # Run the optimization
        best_route, best_cost, best_buses = self.simulated_annealing_optimize(
            self.companies_data.copy(), self.employees, bus_capacity
        )
        
        # Generate schedule
        schedule_text = self.generate_schedule_text(
            best_route, self.employees, bus_capacity, self.route_distance, max_trips
        )
        
        Clock.schedule_once(lambda dt: self.display_results(best_route, best_buses, schedule_text), 0)
    
    def simulated_annealing_optimize(self, companies, employees, bus_capacity):
        current_route = companies.copy()
        current_cost, current_buses = self.calculate_route_cost(current_route, employees, bus_capacity)
        
        best_route = current_route.copy()
        best_cost, best_buses = current_cost, current_buses
        
        temp = 1000
        cooling_rate = 0.98
        
        for i in range(1000):
            Clock.schedule_once(lambda dt, progress=i: self.update_status(f'🔬 Iteration {progress}/1000', progress), 0)
            
            if len(current_route) <= 1:
                break
                
            neighbor = current_route.copy()
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
            
            neighbor_cost, neighbor_buses = self.calculate_route_cost(neighbor, employees, bus_capacity)
            
            delta = neighbor_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_route = neighbor
                current_cost = neighbor_cost
            
            if neighbor_cost < best_cost:
                best_cost = neighbor_cost
                best_buses = neighbor_buses
                best_route = neighbor.copy()
            
            temp *= cooling_rate
        
        return best_route, best_cost, best_buses
    
    def calculate_route_cost(self, route, employees, bus_capacity):
        total_buses = 0
        remaining_employees = copy.deepcopy(employees)
        
        while sum(remaining_employees.values()) > 0 and total_buses < 20:
            total_buses += 1
            remaining_capacity = bus_capacity
            
            for company in route:
                if remaining_employees.get(company, 0) > 0 and remaining_capacity > 0:
                    pickup = min(remaining_employees[company], remaining_capacity, 12)
                    remaining_employees[company] -= pickup
                    remaining_capacity -= pickup
            
            if remaining_capacity == bus_capacity:
                break
        
        empty_seats = max(0, total_buses * bus_capacity - sum(employees.values()))
        cost = total_buses * 1000 + empty_seats * 10
        return cost, total_buses
    
    def generate_schedule_text(self, route, employees, bus_capacity, route_distance, max_trips):
        bus_speed = 30
        pickup_time = 5
        work_hours = 6
        remaining_employees = copy.deepcopy(employees)
        schedule_text = ""
        
        for trip_num in range(1, max_trips + 1):
            # Morning
            trip_start = f"08:{(trip_num-1)*8:02d}"
            current_time = trip_start
            current_distance = 0
            morning_details = []
            remaining_capacity = bus_capacity
            emp_copy = copy.deepcopy(remaining_employees)
            
            for company in route:
                if emp_copy.get(company, 0) > 0 and remaining_capacity > 0:
                    travel_min = (route_distance.get(company, 0) - current_distance) * 60 / bus_speed
                    arrival_time = self.add_minutes(current_time, int(travel_min))
                    
                    pickup_count = min(emp_copy[company], remaining_capacity, 12)
                    emp_copy[company] -= pickup_count
                    remaining_employees[company] -= pickup_count
                    
                    morning_details.append((company, pickup_count, arrival_time))
                    remaining_capacity -= pickup_count
                    current_time = self.add_minutes(arrival_time, pickup_time)
                    current_distance = route_distance.get(company, 0)
            
            # Schedule text formatting
            schedule_text += f"\n🚌 [b]TRIP #{trip_num} - MORNING ARRIVAL[/b]\n"
            schedule_text += f"  🚀 {trip_start} → 🏢 {current_time} | {sum(p for _,p,_ in morning_details)}/{bus_capacity}\n"
            schedule_text += f"  📍 {' → '.join([f'{c}({p})' for c,p,_ in morning_details])}\n\n"
            
            schedule_text += "  Station     Pickup  Arrival  WorkStart  WorkEnd\n"
            schedule_text += "  " + "─" * 50 + "\n"
            for company, count, arrival in morning_details:
                work_start = self.add_minutes(arrival, 15)
                work_end = self.add_hours(work_start, work_hours)
                schedule_text += f"  {company:<10} {count:<7} {arrival:<9} {work_start:<10} {work_end}\n"
        
        return schedule_text
    
    def add_minutes(self, time_str, minutes):
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            new_time = time_obj + timedelta(minutes=minutes)
            return new_time.strftime("%H:%M")
        except:
            return time_str
    
    def add_hours(self, time_str, hours):
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            new_time = time_obj + timedelta(hours=hours)
            return new_time.strftime("%H:%M")
        except:
            return time_str
    
    def update_status(self, text, progress=None):
        self.status_label.text = text
        if progress is not None:
            self.progress_bar.value = (progress / 1000.0) * 1000
    
    def update_progress(self, progress):
        self.progress_bar.value = progress
    
    def display_results(self, best_route, best_buses, schedule_text):
        initial_buses = self.calculate_route_cost(self.companies_data.copy(), self.employees, int(self.bus_capacity.text or 22))[1]
        
        self.results_label.text = f"""
🎯 [color=00ff88][b]OPTIMIZATION COMPLETE![/b][/color]

📊 [b]RESULTS SUMMARY[/b]
• Initial Route: {' → '.join(self.companies_data)}
• [color=ffaa00]Optimized Route:[/color] {' → '.join(best_route)}
• Buses Used: {initial_buses} → [color=00ff00]{best_buses}[/color] ({initial_buses-best_buses} saved!)

{schedule_text}

[color=00ff88]✅ Ready for next optimization![/color]
        """
        self.progress_bar.value = 0
        self.status_label.text = f'✅ Optimization complete! {best_buses} buses needed.'

if __name__ == '__main__':
    TransportOptimizerApp().run()