file(
  GLOB TEST_OPS
  RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
  "test_*.py")
string(REPLACE ".py" "" TEST_OPS "${TEST_OPS}")

foreach(TEST_OP ${TEST_OPS})
  py_test_modules(${TEST_OP} MODULES ${TEST_OP})
endforeach()
if(NOT WIN32)
  set_tests_properties(test_rnn_nets_static PROPERTIES TIMEOUT 120)
  set_tests_properties(test_rnn_nets_static_deprecated PROPERTIES TIMEOUT 120)
  set_tests_properties(test_rnn_nets PROPERTIES TIMEOUT 120)
  set_tests_properties(test_rnn_nets_deprecated PROPERTIES TIMEOUT 120)
endif()
