main: main.o cpl_conn.o
	g++ -o main main.o cpl_conn.o -lcpl -lcpl-odbc -lpthread

main.o: main.cpp
	g++ -c main.cpp

cpl_conn.o: cpl/cpl_conn.cpp cpl/cpl_conn.h
	g++ -c cpl/cpl_conn.cpp

clean:
	rm main.o
	rm cpl_conn.o
	rm main