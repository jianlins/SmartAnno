from conf.ConfigReader import ConfigReader
# ConfigReader(config_file='../conf/smartanno_conf.json').saveStatus(0)


from conf.ConfigReader import ConfigReader
cr=ConfigReader(config_file='../conf/smartanno_conf.json')
cr.setValue('api-key','dd')
print(cr.getValue('api-key'))
