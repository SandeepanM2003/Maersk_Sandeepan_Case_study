import simpy
import random

# Constants
AVG_ARRIVAL_INTERVAL = 5 * 60  # average time between vessel arrivals (5 hours -> minutes)
CONTAINERS_PER_VESSEL = 150
CONTAINER_LIFTING_TIME = 3  # time to lift one container (minutes)
TRUCK_TRANSPORT_TIME = 6  # time for a truck to transport a container (minutes)
SIMULATION_TIME = 24 * 60  # run simulation for 24 hours (minutes)

# Vessel class
class Vessel:
    def __init__(self, env, name, terminal):
        self.env = env
        self.name = name
        self.terminal = terminal
        self.containers = CONTAINERS_PER_VESSEL

    def arrive(self):
        print(f"{self.env.now}: Vessel {self.name} arrived")
        with self.terminal.berths.request() as berth_request:
            yield berth_request
            print(f"{self.env.now}: Vessel {self.name} berthed")
            yield self.env.process(self.unload())

    def unload(self):
        crane = yield self.terminal.cranes.get()
        print(f"{self.env.now}: Crane starts unloading Vessel {self.name}")

        for _ in range(self.containers):
            truck = yield self.terminal.trucks.get()
            print(f"{self.env.now}: Crane lifts container from Vessel {self.name} onto a truck")
            yield self.env.timeout(CONTAINER_LIFTING_TIME)
            self.terminal.trucks.put(truck)
            print(f"{self.env.now}: Truck transports container from Vessel {self.name} to yard")
            yield self.env.timeout(TRUCK_TRANSPORT_TIME)
        
        self.terminal.cranes.put(crane)
        print(f"{self.env.now}: Vessel {self.name} finished unloading and leaves berth")

# Terminal class
class Terminal:
    def __init__(self, env):
        self.env = env
        self.berths = simpy.Resource(env, capacity=2)
        self.cranes = simpy.FilterStore(env, capacity=2)
        for _ in range(2):
            self.cranes.put("Crane")
        self.trucks = simpy.FilterStore(env, capacity=3)
        for _ in range(3):
            self.trucks.put("Truck")

# Vessel generator
def vessel_generator(env, terminal):
    vessel_id = 1
    while True:
        yield env.timeout(random.expovariate(1.0 / AVG_ARRIVAL_INTERVAL))
        vessel = Vessel(env, f"Vessel{vessel_id}", terminal)
        env.process(vessel.arrive())
        vessel_id += 1

# Setup and run simulation
env = simpy.Environment()
terminal = Terminal(env)
env.process(vessel_generator(env, terminal))
env.run(until=SIMULATION_TIME)
