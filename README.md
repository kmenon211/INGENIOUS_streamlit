# Value of Information (VOI) Streamlit App 

## Installation

Install the package and dependencies:

```
pip install -e .
```

## Running Locally

```
streamlit run app.py
```

## Value of Information parameters
Users are able to model a "drill or do nothing" decision and input prior probability of geothermal resource existing. Prior Value and Value of Perfect Information are ouput.

Next, the value of imperfect information is calculated, using a dataframe from various geophysical and geologicial observations around known geothermals systems and other locations deemed not a geothermal resource ("negative").

