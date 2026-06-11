import discord
from discord.ext import commands
import google.generativeai as genai
import json
import traceback
import os

# 🔒 Puxando a chave de forma segura por variável de ambiente
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("⚠️ AVISO: GEMINI_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")
else:
    genai.configure(api_key=GEMINI_KEY)


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO (APENAS VOCÊ MANDA)
        self.CRIADOR_ID = 569633804537430036

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignora mensagens enviadas por outros bots
        if message.author.bot:
            return

        # 2. Verificar se a mensagem é um gatilho para a Aqua
        e_gatilho_aqua = False
        
        # Cenário A: O nome Aqua está na mensagem
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
            
        # Cenário B: É um Reply (resposta) para uma mensagem que a própria Aqua mandou
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        # Se não é para a Aqua, ignora completamente
        if not e_gatilho_aqua:
            return

        # 3. Trava Máxima de Segurança por ID de Usuário
        if message.author.id != self.CRIADOR_ID:
            await message.reply("Apenas o criador Geraldão pode usar a minha IA, pois executo ordens críticas.")
            return

        if not GEMINI_KEY:
            await message.reply("Erro: A chave de API da Aqua não foi configurada no sistema.")
            return

        # Mostra no Discord que ela está a processar
        async with message.channel.typing():
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # PROMPT ETAPA 1: Gerar estritamente o código de execução ou coleta de dados
            prompt_codigo = f"""
            Você é a Aqua, IA administradora do servidor de Discord.
            O criador Geraldão enviou a seguinte mensagem: "{message.content}"
            
            Escreva um código em Python usando a biblioteca discord.py para realizar a ação solicitada ou coletar a informação técnica que ele pediu.
            
            Regras de Ouro:
            - Você tem disponível: `message`, `guild` e `bot`.
            - Se o comando pedir informações (ex: dono, membros, canais), você DEVE salvar o resultado numa variável chamada `resultado_ia`. Exemplo: `resultado_ia = f"O dono é {{guild.owner}}"`
            - Se for apenas uma conversa simples (saudações, perguntas gerais), deixe o código completamente em branco.
            - Responda APENAS com o código puro em formato JSON com a chave "codigo". Sem markdown (```py).
            """
            
            try:
                response_cod = model.generate_content(
                    prompt_codigo,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                dados_codigo = json.loads(response_cod.text)
                codigo_gerado = dados_codigo.get("codigo", "")
                
                resultado_execucao = None
                
                # Se houver código, executa AGORA para obter o resultado antes de falar
                if codigo_gerado and codigo_gerado.strip():
                    ambiente_execucao = {
                        "discord": discord,
                        "message": message,
                        "guild": message.guild,
                        "bot": self.bot,
                        "resultado_ia": None
                    }
                    
                    linhas_codigo = [f"    {linha}" for linha in codigo_gerado.split('\n')]
                    codigo_final = "async def _executar_ia(message, guild, bot):\n" + "\n".join(linhas_codigo)
                    
                    # Compila e roda
                    local_vars = {}
                    exec(codigo_final, ambiente_execucao, local_vars)
                    
                    # Injeta a execução assíncrona
                    await ambiente_execucao["_executar_ia"](message, message.guild, self.bot)
                    
                    # Puxa o resultado modificado pelo código (se houver)
                    if "resultado_ia" in ambiente_execucao and ambiente_execucao["resultado_ia"]:
                        resultado_execucao = ambiente_execucao["resultado_ia"]

                # PROMPT ETAPA 2: Gerar a resposta final em formato de chat conversacional
                contexto_execucao = f"O código técnico foi rodado nos bastidores com sucesso. Resultado real obtido: {resultado_execucao}" if resultado_execucao else "Ação executada com sucesso ou foi apenas uma interação de conversa."
                
                prompt_texto = f"""
                Você é a Aqua. Responda diretamente ao Geraldão sobre a mensagem dele: "{message.content}".
                Contexto real do servidor agora: {contexto_execucao}
                
                Dê uma resposta natural, em formato de texto limpo de chat (sem embeds, sem formatações complexas). Se uma informação técnica foi coletada (como o nome do dono do servidor), use o dado fornecido no Contexto Real para responder de forma exata.
                """
                
                response_texto = model.generate_content(prompt_texto)
                resposta_final = response_texto.text.strip()
                
                # Envia a resposta limpa usando reply
                if resposta_final:
                    await message.reply(resposta_final)
                else:
                    await message.reply("Comando processado com sucesso, Geraldão!")
                    
            except Exception as e:
                erro = traceback.format_exc()
                await message.reply(f"❌ Ocorreu um erro interno ao processar ou executar o comando:\n```py\n{erro}\n```")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
            
