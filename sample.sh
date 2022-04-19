#!/bin/sh

echo "Our compiler uses python >= 3.10"

echo "Cleaning up existing folder if exists"
rm -rf ../out/

echo "Installing Node Packages"
cd client/
npm install
cd ..

echo "Creating out folder"
cd ..
mkdir out
mkdir out/pre
mkdir out/wat
mkdir out/type_check
mkdir out/opt
mkdir out/xml
mkdir out/fact
cd src/

echo "Going through a list of test-programs in the tests folder"

echo "Testing preprocessor"
python3 watc.py ../tests/test-programs/preprocessor_test/simple.c ../tests/test-programs/preprocessor_test/included.c -t preprocessor -o preprocessor.out -tc=False
mv *.out ../out/pre/


echo "Generating XML from the tests folder named: *.xml"
for f in "arithmetic" "control" "funcCall" "simple" "unary" "pointer"
do
    python3 watc.py ../tests/test-programs/$f.c -v xml -o $f.xml -tc=False
done
mv *.xml ../out/xml/

# We no longer are using IR
# echo "Generating IRGen from the tests folder named: *-ir.txt"
# for f in "arithmetic" "control" "funcCall" "simple" "unary" "pointer"
# do
#     python3 watc.py ../tests/test-programs/$f.c -v ir -o $f-ir.txt 2> /dev/null
# done

echo "Generating wat from the tests folder named: *.wat"
for f in "arithmetic" "control" "funcCall" "simple" "unary" "pointer"
do
    python3 watc.py ../tests/test-programs/$f.c -v wat -o $f.wat -tc=False
done
mv *.wat ../out/wat/

echo "Generating optimized wat from the tests folder named: *.wat"
for f in "arithmetic" "control" "funcCall" "simple" "unary" "pointer"
do
    python3 watc.py ../tests/test-programs/$f.c -v wat -o $f.wat -tc=False -op True
done
python3 watc.py ../tests/test-programs/optimization_test/opt.c -v wat -o opt.wat -tc=False -op True
mv *.wat ../out/opt/


echo "Generating wasm from the tests folder named: *.wasm"
for f in "fact" "arithmetic"
do
    python3 watc.py ../tests/test-programs/$f.c -v wasm -o $f.wasm -tc=False
    python3 watc.py ../tests/test-programs/$f.c -v wat -o $f.wat -tc=False
done
cd client/
mv *.wat ../../out/fact/
mv *.wasm ../../out/fact/
cd ..

echo "Generating Type Checker Tests These tests only run the type checker"

for f in "correct" "incorrect_assign" "incorrect_binop" "incorrect_param"
do
    python3 watc.py ../tests/test-programs/typechecker_test/$f.c -v wat -o $f.txt -tco=True > $f.txt
done
mv *.txt ../out/type_check/

echo "Done"
