from application.use_cases.guanacos_spits import GuanacosSpits
from infrastructure.repositories.local_guanacos_repository import LocalGuanacosRepository

def main():
    # Initialize repository and use case following dependency injection principle
    guanacos_repository = LocalGuanacosRepository()
    guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=10)
    
    # Start the workers and run until shutdown
    guanacos_spits.run()

if __name__ == "__main__":
    main()