find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS Test)

add_executable(tst_AutoUpdater tst_AutoUpdater.cpp)

target_link_libraries(tst_AutoUpdater
    PRIVATE
        auto_updater
        Qt${QT_VERSION_MAJOR}::Test
)

add_test(NAME tst_AutoUpdater COMMAND tst_AutoUpdater)
