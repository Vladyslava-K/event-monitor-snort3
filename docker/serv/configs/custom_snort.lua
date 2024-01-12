include '/usr/local/etc/snort/snort.lua'

HOME_NET = 'any'
EXTERNAL_NET = 'any'

ips =
{
    -- use this to enable decoder and inspector alerts
    -- enable_builtin_rules = true,

    variables = default_variables,
    rules = [[
    include /usr/local/etc/rules/pulledpork.rules
    ]]
}

alert_json =
{
    fields = 'gid sid rev timestamp src_addr src_port dst_addr dst_port proto action msg',
    file = true
}

perf_monitor = {  
    modules = { },
    base = true,
    packets = 1,
    seconds = 5,
    output = file, 
    format = 'json',
    summary = false,
}

profiler = {
  modules = {
    show = false
  },
  memory = {
    show = false
  },
  rules = {
    count = 10
  }
}