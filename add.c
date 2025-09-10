#include <stdio.h>

int main() {

int income; 			// 연봉 (원 단위) 
int tax; 				// 소득세 (원 단위) 

scanf("%d", &income);

if(income >= 80000000){
    tax = income*(37/100);
    printf("%d", tax);
}
else if(income >= 40000000) {
    tax = income*(28/100);
    printf("%d", tax);
}
else if(income >= 10000000) {
    tax = income*(19/100);
    printf("%d", tax);
}
else  {
    tax = income*(9.5/100);
    printf("%d", tax);
}

    return 0;
}