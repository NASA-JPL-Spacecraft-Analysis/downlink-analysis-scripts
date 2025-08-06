import setuptools

setuptools.setup(
    name="eurc-gds-fspa-scripts",
    version="4.2.2",
    url="https://github.jpl.nasa.gov/Europa-PESS/fspa-scripts",
    packages=setuptools.find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "aerie_cli @ git+https://github.com/NASA-AMMOS/aerie-cli.git@main",
        "bs4==0.0.2",
        "click==8.0.4",
        "dataclasses-json",
        "eas-parasol==8.1.0",
        "eas-rounds==8.1.0",
        "eurc-fspa-close-the-u==3.1.1",
        "eurc-fspa-dplib==8.2.2",
        "jpl_time",
        "lxml==5.1.0",
        "m20-operational-cloud-store==9.1.0",
        "numpy",
        "pandas",
        "XlsxWriter",
        "xmltodict==0.13.0",
    ],
    py_modules=["fspa_scripts"],
    entry_points={
        "console_scripts": [
            "radmon_to_ctu = fspa_scripts.conversions.radmon_to_ctu:main",
            "chill_to_ctu = fspa_scripts.conversions.chill_to_ctu:main",
            "param_incons_to_ctu = fspa_scripts.conversions.param_incons_to_ctu:main",
            "transpire_process_dps = fspa_scripts.transpire.transpire_process_dps:main",
            "publish_fsw_params = fspa_scripts.parasol.publish_fsw_params:main",
            "param_compare = fspa_scripts.param_compare.param_compare:main",
            "param_history = fspa_scripts.param_history.param_history:main",
            "ctu_csds_states = fspa_scripts.close_the_u.ctu_csds_states:main",
            "merlin_to_ctu_tools = fspa_scripts.ctu_merlin.merlin_to_ctu_tools:main",
            "merlin_to_sm = fspa_scripts.ctu_merlin.merlin_to_sm:main",
            "javadoc_to_sm = fspa_scripts.ctu_merlin.javadoc_to_sm:main"
        ]
    }
)
