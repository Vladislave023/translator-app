// Автоматически сгенерированный код из Python
#include <iostream>
#include <string>

void greet(const std::string& name) {
    std::cout << "Привет, " << name << std::endl;
}

int add_numbers(int x, int y) {
    int result = (x + y);
    return result;
}

int main() {
    greet("Анна");
    add_numbers(7, 8);
    int sum_result = add_numbers(7, 8);
    std::cout << sum_result << std::endl;
    return 0;
}