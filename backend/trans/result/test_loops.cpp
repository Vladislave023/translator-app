// Автоматически сгенерированный код из Python
#include <iostream>
#include <string>

int main() {
    int counter = 1;
    while ((counter <= 5)) {
        std::cout << "Счетчик: " << counter << std::endl;
        counter = (counter + 1);
    }
    int number = 5;
    int factorial = 1;
    int current = 1;
    while ((current <= number)) {
        factorial = (factorial * current);
        current = (current + 1);
    }
    std::cout << "Факториал: " << factorial << std::endl;
    return 0;
}