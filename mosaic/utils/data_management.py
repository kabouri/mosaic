# Technical analysis librairie
# ============================
import pandas as pd
import numpy as np
import pytz
from tzlocal import get_localzone
import random
import itertools
import re
import typing
import pydantic
import pkg_resources
import warnings
from datetime import timedelta, datetime
from ..core import ObjMOSAIC
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


# Misc classes
# ------------
class DataSource(ObjMOSAIC):
    """Basic class for a data source object.
    Meant to be extended by more specific types of data sources.
    """
    dt_start: datetime = pydantic.Field(
        None, description="Starting datetime for the data session")

    dt_end: datetime = pydantic.Field(
        None, description="Ending datetime for the data session")


class DSOHLCV(DataSource):
    """Extends the DataSource class to include additional details
    specifically required for OHLCV (Open/High/Low/Close/Volume) trading data.
    """
    symbol: str = pydantic.Field(
        ..., description="Trading symbol for the asset")

    timeframe: str = pydantic.Field(
        ..., description="Timeframe for the trading data, e.g., 1m, 5m, 1d, etc.")

    dt_start: typing.Union[int, datetime] = pydantic.Field(
        None, description="Session OHLCV current datetime")

    dt_end: typing.Union[int, datetime] = pydantic.Field(
        None, description="Session last closed OHLCV datetime")

    @property
    def dt_s(self):
        # Get local time zone
        local_tz_name = get_localzone().key
        local_tz = pytz.timezone(local_tz_name)
        timeframe_delta = timeframe_to_timedelta(self.timeframe)

        if self.dt_start is None:
            dt_now = local_tz.localize(datetime.now())
            dt_start = round_datetime(dt_now, timeframe_delta)

        elif isinstance(self.dt_start, datetime):
            dt_start = round_datetime(self.dt_start, timeframe_delta)
            
        elif isinstance(self.dt_start, int):
            delta = timeframe_delta*self.dt_start
            dt_start = self.dt_e + delta
            
        else:
            raise ValueError(f"Date start format {self.dt_start} not supported")

        return dt_start if dt_start.tzinfo else local_tz.localize(dt_start)

    @property
    def dt_e(self):
        # Get local time zone
        local_tz_name = get_localzone().key
        local_tz = pytz.timezone(local_tz_name)
        timeframe_delta = timeframe_to_timedelta(self.timeframe)

        if self.dt_end is None:
            dt_now = local_tz.localize(datetime.now())
            dt_end = round_datetime(dt_now, timeframe_delta)

        elif isinstance(self.dt_end, datetime):
            dt_end = round_datetime(self.dt_end, timeframe_delta)
            
        elif isinstance(self.dt_end, int):
            delta = timeframe_delta*self.dt_end
            dt_end = self.dt_s + delta
            
        else:
            raise ValueError(f"Date start format {self.dt_end} not supported")

        return dt_end if dt_end.tzinfo else local_tz.localize(dt_end)

    def dict(self, orders_ids=False, **kwrds):
        self_dict = super().dict(**kwrds)

        if "dt_start" in self_dict:
            self_dict["dt_start"] = self.dt_s

        if "dt_end" in self_dict:
            self_dict["dt_end"] = self.dt_e

        return self_dict
    
    # @pydantic.root_validator(pre=True)
    # def calculate_datetimes(cls, values):
    #     dt_start = values.get('dt_start')
    #     dt_end = values.get('dt_end')
    #     timeframe = values.get('timeframe')
    #     timeframe_delta = timeframe_to_timedelta(timeframe)

    #     if isinstance(dt_start, datetime):
    #         dt_start = round_datetime(dt_start,
    #                                   timeframe_delta)

    #     if isinstance(dt_end, datetime):
    #         dt_end = round_datetime(dt_end,
    #                                 timeframe_delta)
        
    #     if (dt_start is not None) and isinstance(dt_end, int):
    #         delta = timeframe_delta*dt_end
    #         dt_end = dt_start + delta

    #     if dt_end is None:
    #         dt_end = \
    #             round_datetime(datetime.utcnow(), timeframe_delta)
            
    #     if isinstance(dt_start, int):
    #         delta = timeframe_delta*dt_start
    #         dt_start = dt_end + delta

    #     if dt_start is None:
    #         dt_start = \
    #             round_datetime(datetime.utcnow(), timeframe_delta)

    #     values['dt_start'] = dt_start
    #     values['dt_end'] = dt_end

    #     if values['dt_start'] > values['dt_end']:
    #         raise ValueError('dt_start must be smaller than dt_end')
        
    #     return values



class ValueNeighborhood(pydantic.BaseModel):

    lower_bound: float = \
        pydantic.Field(-float("inf"), description="Lower bound")
    upper_bound: float = \
        pydantic.Field(float("inf"), description="Upper bound")
    delta: float = \
        pydantic.Field(0, description="+/- delta from current value")
    step: float = \
        pydantic.Field(1, description="Neighborhood discretization step")

    def domain_from_value(self, value):

        lower_bound = \
            max(value - self.delta, self.lower_bound)
        upper_bound = \
            min(value + self.delta, self.upper_bound)

        if value.__class__ == int:
            dom = list(range(int(lower_bound),
                             int(upper_bound) + 1,
                             int(self.step)))
        else:
            dom = list(np.arange(lower_bound, upper_bound, self.step))

        return dom
    
    def random_neighbor_from_value(self, value):

        lower_bound = \
            max(value - self.delta, self.lower_bound)
        upper_bound = \
            min(value + self.delta, self.upper_bound)
        
        value_new = \
            np.random.uniform(lower_bound, upper_bound)
            
        if value.__class__ == int:
            value_new = round(value_new)

        return value_new


class HyperParams(pydantic.BaseModel):

    def __str__(self):
        return "\n".join(
            [f"{k}: {v}" for k, v in self.dict().items()])

    def random_from_neighbor(
            self,
            neighbor_specs: typing.Dict[str, ValueNeighborhood] = {},
            nchanges=None,
            inplace=False,
    ):
        
        nb_params = len(self.dict())
        if inplace:
            param_new = self
        else:
            param_new = self.copy()

        if nchanges is None:
            nchanges = int(np.ceil(np.random.rand()*nb_params))
        
        params_to_change = \
            random.sample(self.dict().keys(),
                          min(nchanges, nb_params))

        for param_name in params_to_change:

            param_neigh_spec = neighbor_specs.get(param_name)
            if not (param_neigh_spec):
                continue
            param_value_cur = getattr(self, param_name)

            param_value_new = \
                param_neigh_spec.random_neighbor_from_value(param_value_cur)

            setattr(param_new, param_name, param_value_new)

        if not inplace:
            return param_new

    def domain_from_neighbor(
            self,
            neighbor_spec: typing.Dict[str, ValueNeighborhood] = {},
    ):
        
        hparams = {}

        for param, param_spec in neighbor_spec.items():

            param_value_cur = getattr(self, param)
            hparams[param] = \
                param_spec.domain_from_value(param_value_cur)

        return hparams

# Misc functions
# --------------
def round_datetime(dt, delta):
    """
    Round a datetime to the nearest interval specified by a timedelta.
    
    Parameters:
        dt (datetime): The datetime object to be rounded.
        delta (timedelta): The duration of the interval to round to.
        
    Returns:
        datetime: The rounded datetime object.
        
    Summary:
        This function takes a datetime object 'dt' and a timedelta object 'delta' as inputs and rounds the datetime to the nearest interval specified by 'delta'. The function performs the following steps:
        
        1. Convert the timedelta object 'delta' to seconds.
        2. Convert the datetime object 'dt' to a timestamp (number of seconds since 1970-01-01).
        3. Round the timestamp to the nearest multiple of the interval specified by 'delta'.
        4. Convert the rounded timestamp back to a datetime object.
        5. Return the rounded datetime object.
        
        Note that the rounding operation is based on the number of seconds since 1970-01-01, so the precision of the rounding depends on the precision of the input datetime object.
    """
    seconds = delta.total_seconds()
    # Convert the datetime to a timestamp (seconds since 1970-1-1)
    since_epoch = dt.timestamp()
    # Round to the nearest timedelta
    rounded_timestamp = round(since_epoch / seconds) * seconds
    # Convert back to datetime
    rounded_dt = datetime.fromtimestamp(rounded_timestamp)
    
    return rounded_dt


def timeframe_to_seconds(timeframe):
    timeframe_to_sec = \
        {'s': 1, 'm': 60, 'h': 60*60, 'd': 24*60*60}
    timeframe_unit = timeframe[-1]
    timeframe_fact_str = timeframe[:-1]
    timeframe_fact = int(timeframe_fact_str)
    timeframe_nb_sec = timeframe_to_sec[timeframe_unit]

    return timeframe_fact*timeframe_nb_sec


def timeframe_to_timedelta(timeframe):
    value = int(timeframe[:-1])
    unit = timeframe[-1]
    timedelta_unit_map = \
        {'s': "seconds", 'm': "minutes", 'h': "hours", 'd': "days"}
    return timedelta(**{timedelta_unit_map.get(unit): value})


def fmt_currency(val, dec_prec_inf_1=".3", dec_prec_sup_1=".2f"):
    """Utility function to format currency."""
    return "{{val:{prec}}}".format(prec=(dec_prec_inf_1
                                         if val < 1 else dec_prec_sup_1))\
                           .format(val=float(val))


def lag(data, n=0, lag_fmt="{name}[{n}]"):
    """Lag operator
    lag(data_t, n) = data_{t-n}
    """
    warnings.warn("lag is deprecated use Indicator.apply_offset instead",
                  DeprecationWarning)

    data_lag = data.shift(n)
    if isinstance(data_lag, pd.DataFrame):
        data_lag.columns = [lag_fmt.format(
            name=col, n=-n) for col in data_lag.columns]
    else:
        data_lag.name = lag_fmt.format(name=data_lag.name, n=-n)

    return data_lag


def prepare_returns_indic(ret_dfd, indic):
    if isinstance(ret_dfd, pd.DataFrame):
        ret_dfd = {"close": ret_dfd}

    indic_names = list(indic.columns) if isinstance(indic, pd.DataFrame)\
        else [indic.name]

    ret_indic_list = []
    for ret_name, ret_df in ret_dfd.items():

        ret_indic_df = ret_df.stack().rename("returns")\
                                     .reset_index(-1)\
                                     .join(indic)
        ret_indic_df["measure"] = ret_name
        var_order = ["measure"] + indic_names + ["period", "returns"]
        ret_indic_list.append(ret_indic_df[var_order])

    ret_indic_df = pd.concat(ret_indic_list, axis=0)

    return ret_indic_df


def compute_combinations(**params_dict):
    keys, values = zip(*params_dict.items())
    return [dict(zip(keys, v)) for v in itertools.product(*values)]


def join_obj_columns(data_df, sep="|"):

    var_to_joined = data_df.columns
    var_names_joined = sep.join(var_to_joined)
    
    data_join = data_df[var_to_joined[0]].astype(str)
    for var in var_to_joined[1:]:
        data_join = data_join.str.cat(
                data_df[var].astype(str), sep="|")

    data_join.name = var_names_joined

    return data_join


def set_obj_attr_simple(obj, attr_path, value):
    """
    Set the value of a nested attribute or list item in an object.

    Parameters:
        obj (object): The object whose attribute you want to set.
        attr_path (str): The path to the attribute, separated by dots. 
                         For list indices, use square brackets.
        value (any): The value you want to set the attribute to.

    Examples:
        set_nested_attr(bot, "decision_model.pm.features[0].length", 10)
    """
    
    # Split the attribute path using dots and square brackets
    attrs = re.split(r'\.|\[|\]', attr_path)
    # Remove any empty strings resulting from the split
    attrs = list(filter(lambda x: x != '', attrs))
    
    # Traverse the object to the second-last attribute or list item
    for attr in attrs[:-1]:
 
        if attr.isdigit():  # it's a list index
            attr = int(attr)
            obj = obj[attr]
        else:
            obj = getattr(obj, attr)


    # The last attribute or list index whose value we want to set
    last_attr = attrs[-1]
    if last_attr.isdigit():
        last_attr = int(last_attr)

    # Set the value of the last attribute or list item
    if isinstance(last_attr, int):
        obj.__setitem__(last_attr, value)
    else:
        setattr(obj, last_attr, value)


# Recursive function to walk through attributes and set values
def recursive_set(obj, attrs, value):
    """
    Set the value of a nested attribute or list item in an object recursively.

    Parameters:
        obj (object): The object whose attribute you want to set.
        attrs (list): The list of attributes specifying the path to the target attribute.
                      Each attribute in the path can be a regular expression pattern matching multiple keys.
        value (any): The value you want to set the attribute to.

    Examples:
        recursive_set(bot, ["decision_model.pm_*.features[0].length"], 10)
    """
    attr = attrs[0]
    if "*" in attr and not attr.startswith('*'):  # Regex pattern detected
        keys = [key for key in dir(obj) if re.match(attr, key)]
        for key in keys:
            recursive_set(getattr(obj, key), attrs[1:], value)
    elif "*" in attr and attr.startswith('*'):
        attr = attr[1:]
        keys = [key for key in dir(obj) if attr in key]
        if len(attrs) > 1:
            for key in keys:
                recursive_set(getattr(obj, key), attrs[1:], value)
        else:
            for key in keys:
                setattr(obj, key, value)
    else:
        next_obj = obj[int(attr)] if attr.isdigit() else getattr(obj, attr)
        if len(attrs) == 1:  # This is the last attribute, set the value
            if attr.isdigit():
                obj[int(attr)] = value
            else:
                setattr(obj, attr, value)
        else:
            recursive_set(next_obj, attrs[1:], value)


def set_obj_one_attr(obj, attr_path, value):
    """
    Set the value of a nested attribute or list item in an object.
    Supports regular expression matching for keys in the attribute path.

    Parameters:
        obj (object): The object whose attribute you want to set.
        attr_path (str): The path to the attribute, separated by dots.
                         For list indices, use square brackets. Regular
                         expressions can be used to match keys.
        value (any): The value you want to set the attribute to.

    Examples:
        set_obj_one_attr(bot, "decision_model.pm_*.features[0].length", 10)
    """
    # Split the attribute path using dots and square brackets
    attrs = re.split(r'\.|\[|\]', attr_path)
    # Remove any empty strings resulting from the split
    attrs = list(filter(lambda x: x != '', attrs))

    recursive_set(obj, attrs, value)


def set_obj_attrs(obj, attrs):
    """
    Set multiple attributes of an object using a dictionary containing
    attribute-value pairs.

    Parameters:
        obj (object): The object whose attributes you want to set.
        attrs (dict): A dictionary mapping attribute names to their respective
                      values.

    Examples:
        set_obj_attrs(obj, {"attribute1": value1, "attribute2": value2})
    """
    for attr, val in attrs.items():
        set_obj_one_attr(obj, attr, val)


def flatten_dict(d, parent_key=(), level=-1, current_level=0, join_key=None):
    """
    Flatten a nested dictionary.
    
    Parameters:
        d (dict): Dictionary to flatten
        parent_key (tuple): Tuple containing parent keys (used recursively)
        level (int): Maximum level of flattening. Set to -1 to flatten all levels.
        current_level (int): Current level of flattening (used recursively)
        join_key (str, optional): String used to join keys in the resulting flattened dictionary
    
    Returns:
        dict: New flattened dictionary
    
    Example usage:
        nested_dict = {'a': {'b': {'c': 1, 'd': 2}}, 'e': {'f': 3, 'g': {'h': 4}}}
        
        flat_dict_all_levels = flatten_dict(nested_dict)
        print("Flatten all levels:", flat_dict_all_levels)
        # Output: {('a', 'b', 'c'): 1, ('a', 'b', 'd'): 2, ('e', 'f'): 3, ('e', 'g', 'h'): 4}
        
        flat_dict_one_level = flatten_dict(nested_dict, level=1)
        print("Flatten up to level 1:", flat_dict_one_level)
        # Output: {('a', 'b'): {'c': 1, 'd': 2}, ('e', 'f'): 3, ('e', 'g'): {'h': 4}}
        
        flat_dict_two_levels = flatten_dict(nested_dict, level=2)
        print("Flatten up to level 2:", flat_dict_two_levels)
        # Output: {('a', 'b', 'c'): 1, ('a', 'b', 'd'): 2, ('e', 'f'): 3, ('e', 'g', 'h'): 4}
        
        flat_dict_joined_keys = flatten_dict(nested_dict, join_key=".")
        print("Flatten all levels with joined keys:", flat_dict_joined_keys)
        # Output: {'a.b.c': 1, 'a.b.d': 2, 'e.f': 3, 'e.g.h': 4}
    """
    items = {}
    for k, v in d.items():
        new_key = parent_key + (k,)
        if isinstance(v, dict) and (level == -1 or current_level < level):
            items.update(flatten_dict(v, new_key, level, current_level + 1, join_key))
        else:
            if join_key is not None:
                new_key = join_key.join(map(str, new_key))
            items[new_key] = v
    return items


def dict_to_yaml_string(data,
                        indent=0,
                        indent_size=2,
                        indent_char=" ",
                        val_sep="",
                        list_prefix="-"):
    """
    Convert a dictionary (with nested dictionaries and lists) to a YAML-like string representation.
    
    Parameters:
        data (dict): Dictionary to convert
        indent (int): Indentation level (used for recursion)
        indent_size (int): Number of characters used for each indentation level
        indent_char (str): Character used for indentation
        val_sep (str): Character used to separate fields
        list_prefix (str): Character used to prefix list items
    
    Returns:
        str: YAML-like string representation of the dictionary
    
    Example usage:
        example_dict = {
            "name": "John",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "country": {
                    "name": "USA",
                    "code": "US"
                }
            },
            "email": "john@example.com",
            "hobbies": ["reading", {"name": "swimming", "level": "intermediate"}]
        }
        
        yaml_string = dict_to_yaml_string(example_dict)
        print(yaml_string)
    """
    yaml_str = ""
    for key, value in data.items():
        indent_str = indent_char * indent_size * indent  # Calculate the indentation
        yaml_str += indent_str + f"{key}: "
        if isinstance(value, dict):
            yaml_str += val_sep
            yaml_str += dict_to_yaml_string(value, indent + 1, indent_size, indent_char, val_sep, list_prefix)
        elif isinstance(value, list):
            yaml_str += val_sep
            for item in value:
                if isinstance(item, dict):
                    yaml_str += dict_to_yaml_string(item, indent + 1, indent_size, indent_char, val_sep, list_prefix)
                else:
                    yaml_str += indent_str + indent_char * indent_size + f"{list_prefix} {item}{val_sep}"
        else:
            yaml_str += f"{value}{val_sep}"
    return yaml_str


def convert_to_local_time(dt, local_timezone_str=None):
    """
    Converts a datetime object to local time based on the specified local time zone.
    
    Args:
        dt (datetime): Datetime object to convert.
        local_timezone_str (str, optional): String representing the local time zone. 
                                            If None, the system's local time zone will be used.
        
    Returns:
        datetime: Datetime object converted to local time.
    """
    # Obtain the local time zone
    local_tz = pytz.timezone(local_timezone_str) \
        if local_timezone_str else get_localzone()
    
    # Check if the datetime object is tz-aware
    if dt.tzinfo is None:
        # Make the datetime object tz-aware by assuming it is UTC
        dt = pytz.utc.localize(dt)
    
    # Convert to local time
    local_dt = dt.astimezone(local_tz)
    
    return local_dt


def is_iso_datetime(val):
    try:
        datetime.fromisoformat(val.replace('Z', '+00:00'))
        return True
    except Exception:
        return False


def parse_value(val):

    if is_iso_datetime(val):
        val = datetime.fromisoformat(val.replace('Z', '+00:00'))

    if isinstance(val, datetime):
        return convert_to_local_time(val)
    else:
        return val
