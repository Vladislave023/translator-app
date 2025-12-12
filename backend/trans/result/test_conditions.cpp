// Автоматически сгенерированный код из Python
#include <iostream>
#include <string>
#include <vector>
using namespace std;

int main() {
    int age = 18;
    int temperature = 25;
    if ((age >= 18)) {
        cout << "Совершеннолетний" << endl;
    else {
        cout << "Несовершеннолетний" << endl;
        if ((temperature > 30)) {
            cout << "Жарко" << endl;
        else if ((temperature > 20)) {
            cout << "Тепло" << endl;
        else {
            cout << "Прохладно" << endl;
        }
    }
    return 0;
}