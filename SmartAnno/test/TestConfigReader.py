from conf.ConfigReader import ConfigReader
# ConfigReader(config_file='../conf/smartanno_conf2.json').saveStatus(0)


from conf.ConfigReader import ConfigReader
cr=ConfigReader(config_file='../conf/smartanno_conf2.json')
cr.setValue('api-key','dd')
print(cr.getValue('api-key'))
