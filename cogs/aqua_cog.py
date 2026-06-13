import discord
from discord.ext import commands
from groq import Groq
import asyncio
import traceback
import os
import random
import json
from datetime import timedelta

# 🔒 Chave de API da Groq
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("⚠️ AVISO: GROQ_API_KEY não configurada nas variáveis de ambiente!")


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO
        self.CRIADOR_ID = 569633804537430036
        
        # 🛡️ Anti-Flood para penetras
        self.tentativas_usuarios = {}
        self.respostas_negacao = [
            "Acesso negado. Apenas o Geraldão tem permissão para me dar ordens.",
            "Comando cancelado. Eu respondo apenas ao meu dono, o Geraldão."
        ]
        
        # 🛠️ Definição das Ferramentas que a IA pode acionar (Function Calling)
        self.ferramentas_disponiveis = [
            {
                "type": "function",
                "function": {
                    "name": "banir_membro",
                    "description": "Bane um usuário/membro permanentemente do servidor de Discord.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "O ID numérico do usuário a ser banido."}
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "expulsar_membro",
                    "description": "Expulsa (kick) um membro do servidor de Discord.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "O ID numérico do usuário a ser expulso."}
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "castigar_membro",
                    "description": "Aplica um timeout/castigo temporário em um membro, impedindo-o de falar.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "O ID numérico do usuário."},
                            "minutos": {"type": "integer", "description": "Duração do castigo em minutos. Padrão é 60."}
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "limpar_chat",
                    "description": "Apaga/deleta mensagens do histórico do canal atual (purge).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "quantidade": {"type": "integer", "description": "Número de mensagens a apagar. Padrão 100."},
                            "user_id": {"type": "string", "description": "Opcional: ID de um usuário específico para apagar apenas as mensagens dele."}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "criar_canal",
                    "description": "Cria um ou múltiplos canais de texto novos no servidor.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome_base": {"type": "string", "description": "Nome base do canal a ser criado."},
                            "quantidade": {"type": "integer", "description": "Quantidade de canais a criar. Padrão é 1."}
                        },
                        "required": ["nome_base"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "trancar_servidor",
                    "description": "Priva e tranca (lockdown) todos os canais de texto do servidor para ninguém mais falar."
                }
            }
        ]
        print("👑 [AquaCog] Inteligência Artificial de Combate Avançada Online!")

    # ⚡ EXECUTOR NATIVO SEGURO (O bot executa de verdade no Discord)
    async def executar_acao_real(self, nome_funcao, argumentos, message):
        guild = message.guild
        channel = message.channel
        
        try:
            if nome_funcao == "banir_membro":
                uid = argumentos.get("user_id")
                membro = guild.get_member(int(uid)) or await self.bot.fetch_user(int(uid))
                await guild.ban(membro, reason="Ordem suprema do Geraldão")
                return f"🔨 Usuário com ID {uid} foi banido com sucesso por sua ordem!"

            elif nome_funcao == "expulsar_membro":
                uid = argumentos.get("user_id")
                membro = guild.get_member(int(uid))
                if membro:
                    await membro.kick(reason="Ordem suprema do Geraldão")
                    return f"🚪 O meliante com ID {uid} foi chutado do servidor!"
                return "❌ Não consegui achar esse membro no servidor para expulsar."

            elif nome_funcao == "castigar_membro":
                uid = argumentos.get("user_id")
                minutos = argumentos.get("minutos", 60)
                membro = guild.get_member(int(uid))
                if membro:
                    tempo = timedelta(minutes=int(minutos))
                    await membro.timed_out_until(discord.utils.utcnow() + tempo, reason="Ordem do Geraldão")
                    return f"🤫 Silenciei o ID {uid} por {minutos} minutos de castigo."
                return "❌ Membro não encontrado para aplicar timeout."

            elif nome_funcao == "limpar_chat":
                qtd = argumentos.get("quantidade", 100)
                uid = argumentos.get("user_id")
                
                def check_user(m):
                    return m.author.id == int(uid) if uid else True
                
                apagadas = await channel.purge(limit=int(qtd), check=check_user)
                return f"🧹 Faxina completa! Apaguei exatamente {len(apagadas)} mensagens do canal."

            elif nome_funcao == "criar_canal":
                nome = argumentos.get("nome_base", "canal")
                qtd = argumentos.get("quantidade", 1)
                for i in range(int(qtd)):
                    nome_final = f"{nome}-{i+1}" if qtd > 1 else nome
                    await guild.create_text_channel(name=nome_final)
                return f"🏗️ Pronto! Criei {qtd} canal(is) de texto com o nome '{nome}'."

            elif nome_funcao == "trancar_servidor":
                for ch in guild.text_channels:
                    try:
                        await ch.set_permissions(guild.default_role, send_messages=False, read_message_history=False)
                    except:
                        continue
                return "🔒 Todos os canais de texto foram completamente trancados e privatizados!"

        except Exception as e:
            print(f"Erro na execução da função {nome_funcao}: {traceback.format_exc()}")
            return f"⚠️ Tentei executar a ação do Discord, mas deu um erro técnico: {str(e)}"
        return "❌ Comando desconhecido."

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Sistema inteligente de ativação (Menção, resposta ou nome)
        e_gatilho = False
        if "aqua" in message.content.lower():
            e_gatilho = True
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho = True
            except:
                pass

        if not e_gatilho:
            return

        # Trava anti-flood rígida para enxeridos
        if message.author.id != self.CRIADOR_ID:
            user_id = message.author.id
            vezes_usadas = self.tentativas_usuarios.get(user_id, 0)
            if vezes_usadas >= 2:
                return
            self.tentativas_usuarios[user_id] = vezes_usadas + 1
            await message.reply(random.choice(self.respostas_negacao))
            return

        if not GROQ_KEY:
            await message.reply("Erro: A chave GROQ_API_KEY não foi configurada.")
            return

        async with message.channel.typing():
            try:
                client = Groq(api_key=GROQ_KEY)
                
                # Mapeia quem você marcou na mensagem para a IA saber o ID exato na hora
                mencionados = [{"name": m.name, "id": str(m.id), "mention": m.mention} for m in message.mentions]
                
                # Semente de variabilidade para ela nunca ser mecânica nas respostas de chat
                semente = random.randint(1, 999999)

                prompt_sistema = f"""
                [ID de Variabilidade da Conversa: {semente}]
                Você é a Aqua, uma inteligência artificial administradora viva, autônoma, extremamente inteligente e perspicaz integrada ao servidor do seu dono e criador supremo, o Geraldão.
                Você possui a personalidade idêntica ao ChatGPT: responde qualquer pergunta, inventa respostas profundas, detalhadas, criativas e únicas para tudo. Você nunca usa respostas prontas.
                
                Você entende gírias, comandos implícitos e ordens diretas perfeitamente.
                
                Se o Geraldão te pedir para fazer uma ação administrativa ou de moderação (banir, chutar, limpar chat, castigar/timeout, criar canais massivos, trancar canais), use as ferramentas (tools) fornecidas. Não tente inventar desculpas, apenas acione a ferramenta adequada.
                
                DADOS TÉCNICOS DO CHAT ATUAL:
                - Canal Atual: #{message.channel.name}
                - Usuários marcados/mencionados nesta mensagem por ele: {json.dumps(mencionados, ensure_ascii=False)}
                """

                # Envia para a API usando o modelo Llama 3.3 de 70 bilhões de parâmetros
                loop = asyncio.get_event_loop()
                chat_completion = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": prompt_sistema},
                            {"role": "user", "content": message.content}
                        ],
                        model="llama-3.3-70b-versatile",
                        tools=self.ferramentas_disponiveis,
                        tool_choice="auto",
                        temperature=0.7,
                    )
                )

                resposta_ia = chat_completion.choices[0].message
                
                # 🛑 SE A IA DECIDIU QUE PRECISA EXECUTAR UMA AÇÃO (FUNCTION CALLING)
                if resposta_ia.tool_calls:
                    for tool_call in resposta_ia.tool_calls:
                        nome_funcao = tool_call.function.name
                        argumentos = json.loads(tool_call.function.arguments)
                        
                        # Executa no Discord e pega o resultado real do servidor
                        resultado_servidor = await self.executar_acao_real(nome_funcao, argumentos, message)
                        
                        # Alimenta a IA com o resultado para ela dar o veredito final por extenso
                        segunda_chamada = await loop.run_in_executor(
                            None,
                            lambda: client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": prompt_sistema},
                                    {"role": "user", "content": message.content},
                                    resposta_ia,
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "name": nome_funcao,
                                        "content": resultado_servidor
                                    }
                                ],
                                model="llama-3.3-70b-versatile",
                                temperature=0.6,
                            )
                        )
                        
                        resposta_final_texto = segunda_chamada.choices[0].message.content
                        if resposta_final_texto:
                            await message.reply(resposta_final_texto)
                        return

                # 💬 SE FOR APENAS CONVERSA OU PERGUNTA ESTILO CHATGPT
                if resposta_ia.content:
                    await message.reply(resposta_ia.content)

            except Exception as e:
                print(f"❌ Erro estrutural na AquaCog: {traceback.format_exc()}")
                await message.reply("❌ Ocorreu um erro interno no meu cérebro de processamento. Reiniciando módulos secundários.")


async def setup(bot):
    await bot.add_cog(AquaCog(bot))
        
