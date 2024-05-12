from controllable_qt.driver import Driver

if __name__ == "__main__":
    driver = Driver({"starting_url":'http://httpbin.org/get'})
    driver.execute_script_file("main.js")
    input("")