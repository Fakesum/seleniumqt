from seleniumqt.driver import Driver

if __name__ == "__main__":
    driver = Driver({"starting_url":'http://httpbin.org/get'})
    driver.execute_script_file("main.js")
    driver.open("https://www.google.com")
    input("")