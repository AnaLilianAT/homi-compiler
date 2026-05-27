# Demo

Arquivos preparados para a apresentacao final:

- `01_valido_simples.homi`: trigger de estado, condicao de estado, ligar luz, delay e desligar luz
- `02_valido_professor_complexo.homi`: multiplos triggers, condicao de horario, `if/then/else`, `choose`, `service action`, `notify` e `mode restart`
- `03_erro_sintatico.homi`: erro sintatico com recuperacao por modo panico
- `04_erro_semantico.homi`: erro semantico ao tentar ligar um sensor

Comandos recomendados:

```bash
make demo-valid
make demo-syntax-error
make demo-semantic-error
```
